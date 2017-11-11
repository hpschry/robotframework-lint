from rflint.common import TestRule, KeywordRule, GeneralRule, PostRule, ERROR, WARNING
from rflint.parser.rfkeyword import Keyword

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

class StoreKW (KeywordRule):
    '''Pseudo rule to store all keyword information in a list.

    Put the keyword objects in a list as they are traversed.
    This is for later processing (finding similar keyword 
    names and bodies.'''

    kw_list = []

    def apply (self, keyword):
        self.kw_list.append (keyword)


class KWRedundantName (PostRule):
    '''Determine redundant resp. similar keyword names.
    
    Based on the assumption, that very similar keyword names
    might indicate duplicate or similar implementations.

    Note: it might make sense to set the upper threshold (high) 
    to a value slightly smaller than 1.0 to exclude similarities
    that were created by intent (e.g. multiple setup suite 
    implementations).

    Based on the approach described in:
    http://stackoverflow.com/questions/8897593/similarity-between-two-text-documents'''

    cosphi_low = 0.9
    cosphi_high = 1.0

    def configure (self, low, high):
        self.cosphi_low = float (low)
        self.cosphi_high = float (high)
    
    def apply (self, dummy):
        kw_names = [k.name for k in StoreKW.kw_list]
        tfidf = TfidfVectorizer().fit_transform(kw_names)
        pwsim = tfidf * tfidf.T
        count = 0
        for i, r in enumerate (pwsim.A [:-1]):
            for j, cosphi in enumerate (r [i+1:], start=i+1):
                if (cosphi >= self.cosphi_low) and (cosphi <= self.cosphi_high):
                    count = count + 1
                    src_kw = StoreKW.kw_list [i]
                    trg_kw = StoreKW.kw_list [j]
                    msg = "High keyword name similarity ({}) - redundant?\n  {} ({}, {})\n  {} ({}, {})".format (
                        cosphi, src_kw.name, src_kw.path, src_kw.linenumber, trg_kw.name, trg_kw.path, trg_kw.linenumber)
                    self.report (src_kw, msg, 0)
        msg = "W: High keyword name similarity ({} <= cosphi <= {}) count is {}".format (
            self.cosphi_low, self.cosphi_high, count)
        print (msg)
        

class KWRedundantBody (PostRule):
    '''Determine redundant resp. similar keyword implementations.
    
    Based on the assumption, that very similar keyword implementations
    might indicate duplicate or similar implementations.

    Based on the approach described in:
    http://stackoverflow.com/questions/8897593/similarity-between-two-text-documents'''

    cosphi_low = 0.9
    cosphi_high = 1.0

    def configure (self, low, high):
        self.cosphi_low = float (low)
        self.cosphi_high = float (high)
    
    def apply (self, dummy):
        
        kw_bodies = ["\n".join ([r.raw_text for r in kw.rows]) for kw in StoreKW.kw_list]
        tfidf = TfidfVectorizer().fit_transform(kw_bodies)
        pwsim = tfidf * tfidf.T
        count = 0
        for i, r in enumerate (pwsim.A [:-1]):
            for j, cosphi in enumerate (r [i+1:], start=i+1):
                if (cosphi >= self.cosphi_low) and (cosphi <= self.cosphi_high):
                    count += 1
                    src_kw = StoreKW.kw_list [i]
                    trg_kw = StoreKW.kw_list [j]
                    msg = "High keyword body similarity ({}) - redundant?\n  {} ({}, {})\n  {} ({}, {})".format (
                        cosphi, src_kw.name, src_kw.path, src_kw.linenumber, trg_kw.name, trg_kw.path, trg_kw.linenumber)
                    self.report (src_kw, msg, 0)
        msg = "W: High keyword body similarity ({} <= cosphi <= {}) count is {}".format (
            self.cosphi_low, self.cosphi_high, count)
        print (msg)

    
