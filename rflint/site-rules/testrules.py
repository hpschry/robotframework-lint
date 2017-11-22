from rflint.common import TestRule, KeywordRule, GeneralRule, PostRule, ERROR, WARNING
from rflint.parser.rfkeyword import Keyword

from numpy import finfo
from sklearn.feature_extraction.text import TfidfVectorizer

import re

"""
class DummyRule (GeneralRule):

    def apply (self, robot_file):
        self.report (robot_file, "*** Some dummy rule ***", 0, 0)


class DummyKeywordRule (KeywordRule):

    def apply (self, robot_file):
        self.report (robot_file, "*** Some dummy keyword rule ***", 0, 0)
"""
    
class NameContainsUnbalancedQuotes (KeywordRule):
    '''Simple rule checking for balanced quotes in keyword names'''

    def apply (self, keyword):
        if keyword.name.count('"') % 2 <> 0:
            msg = "Unbalanced quotes in keyword name '%s'" % keyword.name
            self.report (keyword, msg, 0)

