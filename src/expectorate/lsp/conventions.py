""" typographical conventions for working with LSP markdown specs
"""
from dataclasses import dataclass
from typing import Text


@dataclass
class SpecConvention:
    version: Text
    preamble_separator: Text
    epilogue_separator: Text
    feature_separator: Text


@dataclass
class Version314(SpecConvention):
    version: Text = "3.14"
    preamble_separator: Text = "#### $ Notifications and Requests"
    epilogue_separator: Text = "### Implementation considerations"
    feature_separator: Text = "#### <a href"


@dataclass
class Version315(Version314):
    """ minor change to avoid additional non-features
    """

    version: Text = "3.15"
    preamble_separator: Text = "#### Server lifetime"


CONVENTIONS = {
    "3.14": Version314(),
    "3.15": Version315(),
}
