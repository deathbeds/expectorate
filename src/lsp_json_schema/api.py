# import copy
# import json
# import jinja2
# import jsonschema
# import pytest
# import yaml

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Text

import pandas
import pyemojify

from . import constants
from .utils import ensure_js_package, ensure_repo


@dataclass
class Generator:
    workdir: Path
    output: Path

    lsp_dir: Optional[Path] = None
    vlspn_dir: Optional[Path] = None

    lsp_repo = constants.LSP_REPO
    lsp_committish = constants.LSP_COMMIT
    lsp_spec_version = constants.LSP_SPEC_VERSION

    vlspn_repo = constants.VLSPN_REPO
    vlspn_committish = constants.VLSPN_COMMIT

    prettier_version = constants.PRETTIER_VERSION
    tssg_version = constants.TSSG_VERSION

    raw_spec: Optional[Text] = None
    naive_schema: Optional[Dict[Text, Any]] = None
    spec_features: Optional[List[Text]] = None
    df: Optional[pandas.DataFrame] = None

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
                / f"""specification-{self.lsp_spec_version.replace('.', '-')}.md"""
            )
            self.raw_spec = spec_md.read_text()

    def ensure_js_deps(self):
        if self.vlspn_dir is not None:
            ensure_js_package(self.vlspn_dir, constants.TSSG, self.tssg_version)
            ensure_js_package(self.vlspn_dir, "prettier", self.prettier_version)

    def build_naive_schema(self):
        if self.vlspn_dir is not None:
            proto = self.vlspn_dir / "protocol"
            self.naive_schema = json.loads(
                subprocess.check_output(
                    [
                        "node",
                        self.vlspn_dir / "node_modules" / ".bin" / constants.TSSG,
                        "--path",
                        proto / "src" / "protocol.ts",
                        "--expose",
                        "all",
                    ],
                    cwd=proto,
                ).decode("utf-8")
            )

    def extract_spec_features(self):
        if self.raw_spec:
            self.spec_features = (
                self.raw_spec.split("#### $ Notifications and Requests")[1]
                .split("### Implementation considerations")[0]
                .split("#### <a href")[1:]
            )

    def init_df(self):
        if self.spec_features:
            df = pandas.DataFrame(self.spec_features, columns=["_md"])
            md = df["_md"]
            df["method"] = md.apply(
                lambda md: re.findall(r"""\* method: '(.*)'""", md)[0]
            )
            df["_raw_params"] = md.apply(
                lambda md: re.findall(r"""\* params: (.*)""", md)[0]
            )
            df["title"] = md.apply(
                lambda md: md.split(">")[1].split("<")[0].strip().split("(")[0].strip()
            )
            df["type"] = md.apply(
                lambda md: pyemojify.emojify(
                    md.split(">")[1].split("<")[0].strip().split("(")[1]
                )
                .replace(")", "")
                .strip()
            )
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
        def parse_params(rp, p, schema):
            if p in schema["definitions"]:
                return schema["definitions"][p]
            if rp in ["void", "none"]:
                return {"type": "null"}
            if rp in ["'any'"]:
                return {}
            return None

        if self.df is not None:
            self.df["params"] = self.df["_raw_params"].apply(
                lambda rp: (re.findall(r"`(.*?)`", rp) or [None])[0]
            )

            self.df["params_schema"] = [
                parse_params(row["_raw_params"], row["params"], self.naive_schema)
                for row in self.df[["_raw_params", "params"]].to_dict(orient="records")
            ]
            print("with annotated params:")
            print(self.df)

    def annotate_results(self):
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

        if self.df is not None:
            self.df["result"] = self.df["_raw_result"].apply(
                lambda rr: parse_results(rr)
            )
            print("with annotated results:")
            print(self.df)

    def annotate_result_schema(self):
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
                print(r)
                print(f"\t{opts}")
                return None
            return {"oneOf": opts}

        if self.df is not None:
            self.df["result_schema"] = self.df["result"].apply(
                lambda rr: result_to_schema(rr, self.naive_schema)
            )
            print("with annotated result_schema:")
            print(self.df[["result"]])

    def check_results(self):
        assert self.df is not None
        check = self.df[self.df["result"].apply(lambda x: x is None)][
            ~self.df["_raw_result"].isnull()
        ][["_raw_result", "result"]]
        assert check.shape[0] == 0, "unparsed results"

    def annotate_method_titles(self):
        def method_title(m):
            name = "".join([b[0].upper() + b[1:] for b in m.split("/") if b != "$"])
            return name

        if self.df is not None:
            self.df["ns_title"] = list(
                self.df.reset_index()["method"].apply(method_title)
            )

            print("With method titles:")
            print(self.df[["ns_title"]])

    def annotate_result_titles(self):
        def ns_result(r):
            if r is None:
                return None
            try:
                r = re.sub(r"\b([A-Z])", "proto.\\1", r)
            except Exception as err:  # pragma: no cover
                print(err, r)
            return r

        if self.df is not None:
            self.df["ns_result"] = self.df["result"].apply(ns_result)
            print("With result titles:")
            print(self.df[["ns_title"]])
