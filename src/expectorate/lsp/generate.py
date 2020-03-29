import json
import logging
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Text

import jinja2
import jsonschema
import pandas
import pyemojify

from ..utils import ensure_js_package, ensure_repo
from . import constants
from .conventions import CONVENTIONS, SpecConvention


@dataclass
class SpecGenerator:
    workdir: Path
    output: Path
    log: logging.Logger

    lsp_dir: Optional[Path] = None
    vlspn_dir: Optional[Path] = None

    lsp_spec: SpecConvention = CONVENTIONS[constants.LSP_SPEC_VERSION]

    lsp_repo: Text = constants.LSP_REPO
    lsp_committish: Text = constants.LSP_COMMIT

    vlspn_repo: Text = constants.VLSPN_REPO
    vlspn_committish: Text = constants.VLSPN_COMMIT

    prettier_version: Text = constants.PRETTIER_VERSION
    tssg_version: Text = constants.TSSG_VERSION

    raw_spec: Optional[Text] = None

    spec_features: Optional[List[Text]] = None

    naive_schema: Optional[Dict[Text, Any]] = None
    synthetic_schema: Optional[Dict[Text, Any]] = None

    df: Optional[pandas.DataFrame] = None

    def vlspn_bin(self, cmd: Text) -> List[Text]:
        assert self.vlspn_dir is not None
        return ["node", str(self.vlspn_dir / "node_modules" / ".bin" / cmd)]

    def generate(self) -> int:
        self.ensure_repos()
        self.parse_spec()
        self.ensure_js_deps()
        self.build_naive_schema()
        self.extract_spec_features()
        # do data munging
        self.init_df()
        self.annotate_params()
        self.annotate_results()
        self.annotate_result_schema()
        self.check_results()
        self.annotate_method_titles()
        self.annotate_result_titles()
        self.write_protocol_schema_ts()
        self.build_synthetic_schema()

        # post-test
        self.validate_synthetic_schema()
        self.annotate_params_schema()
        self.reannotate_result_schema()
        self.validate_final_schema()

        return 0

    def ensure_repos(self):
        if not self.workdir.exists():
            self.workdir.mkdir(parents=True)

        self.lsp_dir = ensure_repo(self.workdir, self.lsp_repo, self.lsp_committish)
        self.vlspn_dir = ensure_repo(
            self.workdir, self.vlspn_repo, self.vlspn_committish
        )

    def parse_spec(self):
        if self.lsp_dir is not None:
            spec_md = (
                self.lsp_dir
                / "_specifications"
                / f"""specification-{self.lsp_spec.version.replace('.', '-')}.md"""
            )
            self.raw_spec = spec_md.read_text()

    def ensure_js_deps(self):
        if self.vlspn_dir is not None:
            ensure_js_package(self.vlspn_dir, constants.TSSG, self.tssg_version)
            ensure_js_package(self.vlspn_dir, "prettier", self.prettier_version)

    @property
    def naive_schema_path(self) -> Path:
        return self.output / f"lsp.{self.lsp_spec.version}.naive.schema.json"

    def build_naive_schema(self):
        assert self.vlspn_dir is not None
        proto = self.vlspn_dir / "protocol"
        self.naive_schema = json.loads(
            subprocess.check_output(
                [
                    *self.vlspn_bin(constants.TSSG),
                    "--path",
                    proto / "src" / "protocol.ts",
                    "--expose",
                    "all",
                ],
                cwd=proto,
            ).decode("utf-8")
        )
        if not self.output.exists():
            self.output.mkdir(parents=True)
        self.naive_schema_path.write_text(
            json.dumps(self.naive_schema, indent=2, sort_keys=True)
        )

    def extract_spec_features(self):
        assert self.raw_spec

        after_notifications = self.raw_spec.split(self.lsp_spec.preamble_separator)[1]

        before_implementations = after_notifications.split(
            self.lsp_spec.epilogue_separator
        )[0]

        self.spec_features = before_implementations.split(
            self.lsp_spec.feature_separator
        )[1:]

    def init_df(self):
        assert self.spec_features

        df = pandas.DataFrame(self.spec_features, columns=["_md"])
        md = df["_md"]

        def _find_method(md: Text):
            try:
                return re.findall(r"""\* method: '(.*)'""", md)[0]
            except IndexError:
                return None

        df["method"] = md.apply(_find_method)

        not_methods = df[pandas.isna(df["method"])]
        if len(not_methods) > 0:
            self.log.warning("dropping %s non-methods:", len(not_methods))
            self.log.warning(not_methods)
            df = df[pandas.notna(df["method"])]

        df["_raw_params"] = md.apply(
            lambda md: (re.findall(r"""\* params: (.*)""", md) or [None])[0]
        )
        df["title"] = md.apply(
            lambda md: md.split(">")[1].split("<")[0].strip().split("(")[0].strip()
        )

        def _find_type(md: Text):
            try:
                return (
                    pyemojify.emojify(
                        md.split(">")[1].split("<")[0].strip().split("(")[1]
                    )
                    .replace(")", "")
                    .strip()
                )
            except IndexError:
                return None

        df["type"] = md.apply(_find_type)
        df["_raw_result"] = md.apply(
            lambda md: (
                re.findall(r"""\* result: (.*)""", md, flags=re.M | re.I) or [None]
            )[0]
        )
        df["_raw_error"] = md.apply(
            lambda md: (
                re.findall(r"""\* error: (.*)""", md, flags=re.M | re.I) or [None]
            )[0]
        )
        self.df = df.sort_values(["type", "method"]).set_index(["type", "method"])

    def annotate_params(self):
        assert self.df is not None

        def parse_params(rp, p, schema):
            if p in schema["definitions"]:
                return schema["definitions"][p]
            if rp in ["void", "none"]:
                return {"type": "null"}
            if rp in ["'any'"]:
                return {}
            return None

        self.df["params"] = self.df["_raw_params"].apply(
            lambda rp: None if rp is None else (re.findall(r"`(.*?)`", rp) or [None])[0]
        )

        self.df["params_schema"] = [
            parse_params(row["_raw_params"], row["params"], self.naive_schema)
            for row in self.df[["_raw_params", "params"]].to_dict(orient="records")
        ]
        self.log.debug("with annotated params:")
        self.log.debug(self.df)

    def annotate_results(self):
        assert self.df is not None

        def parse_results(rr):
            if rr in [None]:
                return rr
            r = (
                rr.replace("defined as follows:", "")
                .replace("`", "")
                .replace("the selected", "")
                .replace(r"\|", "|")
                .replace("An array of DocumentLink", "DocumentLink[]")
            )
            r = re.sub(r"\[(.*?)\]\(#.+\)", "\\1", r).strip()
            for splitter in [" where ", " describing ", " as defined ", ". ", " if "]:
                r = r.split(splitter)[0].strip()
            if r.endswith("."):
                r = r[:-1]
            return r

        self.df["result"] = self.df["_raw_result"].apply(lambda rr: parse_results(rr))
        self.log.debug("with annotated results:")
        self.log.debug(self.df)

    def annotate_result_schema(self):
        assert self.df is not None

        def result_to_schema(r, schema):  # pragma: no cover
            if not r:
                return r
            opts = []
            if r in ["void", "void."]:
                return {"type": "null"}

            for sr in [sr.strip() for sr in r.split(r"\|")]:
                is_arr = False
                if sr.endswith("[]"):
                    is_arr = True
                    sr = sr[:-2]
                if sr.startswith("null"):
                    sr = {"type": "null"}
                elif sr.startswith("void"):
                    sr = {"type": "null"}
                elif sr in schema["definitions"]:
                    sr = {"$ref": f"#/definitions/{sr}"}
                    if is_arr:
                        sr = {"type": "array", "items": sr}
                opts += [sr]
            if str in [type(sr) for sr in opts]:
                self.log.warning(r)
                self.log.warning(f"\t{opts}")
                return None
            return {"oneOf": opts}

        self.df["result_schema"] = self.df["result"].apply(
            lambda rr: result_to_schema(rr, self.naive_schema)
        )
        self.log.debug("with annotated result_schema:")
        self.log.debug(self.df[["result"]])

    def check_results(self):
        assert self.df is not None
        check = self.df[self.df["result"].apply(lambda x: x is None)][
            ~self.df["_raw_result"].isnull()
        ][["_raw_result", "result"]]
        assert check.shape[0] == 0, "unparsed results"

    def annotate_method_titles(self):
        assert self.df is not None

        def method_title(m):
            name = "".join([b[0].upper() + b[1:] for b in m.split("/") if b != "$"])
            return name

        self.df["ns_title"] = list(self.df.reset_index()["method"].apply(method_title))

        self.log.debug("With method titles:")
        self.log.debug(self.df[["ns_title"]])

    def ns_result(self, r: Text) -> Text:
        if r is None:
            return None
        try:
            r = re.sub(r"\b([A-Z])", "proto.\\1", r)
        except Exception as err:  # pragma: no cover
            self.log.error("Error applying namespace title: %s %s", r, err)
        return r

    def annotate_result_titles(self):
        assert self.df is not None
        self.df["ns_result"] = self.df["result"].apply(self.ns_result)
        self.log.debug("With result titles:")
        self.log.debug(self.df[["ns_title"]])

    def write_protocol_schema_ts(self):
        assert self.df is not None
        assert self.vlspn_dir is not None
        tmpl = jinja2.Template(
            (Path(__file__).parent / "templates" / "protocol-schema.ts.j2").read_text()
        )

        out = self.vlspn_dir / "protocol" / "src" / "protocol-schema.ts"

        out.write_text(
            tmpl.render(
                rows=self.df.reset_index().to_dict(orient="records"),
                ns_result=self.ns_result,
            )
        )
        subprocess.check_call([*self.vlspn_bin("prettier"), "--write", out])

    @property
    def synthetic_schema_path(self) -> Path:
        return self.output / f"lsp.{self.lsp_spec.version}.synthetic.schema.json"

    def build_synthetic_schema(self):
        assert self.vlspn_dir is not None
        proto = self.vlspn_dir / "protocol"
        self.synthetic_schema = json.loads(
            subprocess.check_output(
                [
                    *self.vlspn_bin(constants.TSSG),
                    "--path",
                    proto / "src" / "protocol-schema.ts",
                    "--expose",
                    "all",
                    "--type",
                    "_AnyFeature",
                ],
                cwd=proto,
            ).decode("utf-8")
        )
        self.synthetic_schema_path.write_text(
            json.dumps(self.naive_schema, indent=2, sort_keys=True)
        )

    def validate_synthetic_schema(self):
        jsonschema.validators.Draft7Validator(self.synthetic_schema)

    def annotate_params_schema(self):
        assert self.df is not None
        assert self.synthetic_schema is not None

        self.df["params_schema"] = self.df["ns_title"].apply(
            lambda x: None
            if x is None
            else self.synthetic_schema["definitions"][f"_{x}Request"]["properties"][
                "params"
            ]
            if f"_{x}Request" in self.synthetic_schema["definitions"]
            else None
        )
        self.log.debug("final params schema:")
        self.log.debug(self.df[["params", "params_schema"]])

    def reannotate_result_schema(self):
        assert self.df is not None
        assert self.synthetic_schema is not None

        self.df["result_schema"] = self.df["ns_title"].apply(
            lambda x: self.synthetic_schema["definitions"][f"_{x}Response"][
                "properties"
            ]["result"]
            if f"_{x}Response" in self.synthetic_schema["definitions"]
            else None
        )
        self.log.debug("final result schema:")
        self.log.debug(self.df[["result", "result_schema"]])

    def validate_final_schema(self):
        assert self.df is not None
        missing_params = self.df[self.df["params_schema"].isnull()][
            ["_raw_params", "params", "params_schema"]
        ]
        missing_results = self.df[self.df["result"].isnull()][
            ~self.df["_raw_result"].isnull()
        ][["_raw_result", "result", "result_schema"]]

        if len(missing_params):  # pragma: no cover
            self.log.error("missing params:")
            self.log.error(missing_params)
        if len(missing_results):  # pragma: no cover
            self.log.error("missing results:")
            self.log.error(missing_results)

        assert not len(missing_params) and not len(missing_results)
