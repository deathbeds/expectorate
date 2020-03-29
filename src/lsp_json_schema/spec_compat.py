from dataclasses import dataclass
from typing import Text


@dataclass
class SpecVersion:
    version: Text
    preamble_separator: Text
    epilogue_separator: Text
    feature_separator: Text


@dataclass
class Version314(SpecVersion):
    version: Text = "3.14"
    preamble_separator: Text = "#### $ Notifications and Requests"
    epilogue_separator: Text = "### Implementation considerations"
    feature_separator: Text = "#### <a href"


@dataclass
class Version315(Version314):
    version: Text = "3.15"
    preamble_separator: Text = "#### Server lifetime"


VERSIONS = {"3.14": Version314(), "3.15": Version315()}
