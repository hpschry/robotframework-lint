from rflint.common import TestRule, KeywordRule, GeneralRule, PostRule, ERROR, WARNING
from rflint.parser.rfkeyword import Keyword
from rflint.parser.testcase import Testcase

from numpy import finfo, argwhere, logical_and, nonzero, fill_diagonal, sort
from sklearn.feature_extraction.text import TfidfVectorizer

import re

class PairwiseSimilarity (object):
    
    def find (self, cos_lower, cos_upper, doc_list):
        print (str(doc_list))
        tfidf = TfidfVectorizer().fit_transform(doc_list)
        print ("tfidf:\n" + str (tfidf.A))
        pwsim_array = (tfidf * tfidf.T).A
        count = 0
        fill_diagonal (pwsim_array, 0)
        print ("pwsim:\n" + str (pwsim_array))
        cos_lower -= finfo("float64").eps
        cos_upper += finfo("float64").eps
        similars = argwhere (
            logical_and (pwsim_array >= cos_lower, cos_upper >= pwsim_array))
        print ("unsorted:\n" + str (similars))
        sorted_similars = similars[similars[:,1].argsort()]
        print ("sorted:\n" + str (sorted_similars))
        return sorted_similars
    """
        print ("argwhere:\n" + str ()
        for i, r in enumerate (pwsim.A [:-1]):
            for j, cosphi in enumerate (r [i+1:], start=i+1):
                # print (i, j, cosphi)
                if (cosphi >= self.cosphi_low) and (cosphi <= self.cosphi_high + finfo("float64").eps):
                    count += 1
                    src_kw = StoreKW.kw_list [i]
                    trg_kw = StoreKW.kw_list [j]
                    msg = "High keyword body similarity ({}) - redundant?\n  {} ({}, {})\n  {} ({}, {})".format (
                        cosphi, src_kw.name, src_kw.path, src_kw.linenumber, trg_kw.name, trg_kw.path, trg_kw.linenumber)
                    self.report (src_kw, msg, 0)
        msg = "W: High keyword body similarity ({} <= cosphi <= {}) count is {}".format (
            self.cosphi_low, self.cosphi_high, count)
        print (msg)
    """


    

class StoreTest (TestRule):
    """Pseudo rule to store all test information in a list.
    """
    test_list = []

    def apply (self, testcase):
        self.test_list.append (testcase)
        

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
        similars = PairwiseSimilarity().find(self.cosphi_low, self.cosphi_high, kw_bodies)
        print (similars)


    """
        print (str(kw_bodies))
        tfidf = TfidfVectorizer().fit_transform(kw_bodies)
        print ("tfidf:\n" + str (tfidf.A))
        pwsim = tfidf * tfidf.T
        print ("pwsim:\n" + str (pwsim.A))
        count = 0
        arr = pwsim.A
        fill_diagonal (arr, 0)
        print ("argwhere:\n" + str (argwhere (logical_and (arr >= self.cosphi_low, self.cosphi_high + finfo("float64").eps >= arr))))
        for i, r in enumerate (pwsim.A [:-1]):
            for j, cosphi in enumerate (r [i+1:], start=i+1):
                # print (i, j, cosphi)
                if (cosphi >= self.cosphi_low) and (cosphi <= self.cosphi_high + finfo("float64").eps):
                    count += 1
                    src_kw = StoreKW.kw_list [i]
                    trg_kw = StoreKW.kw_list [j]
                    msg = "High keyword body similarity ({}) - redundant?\n  {} ({}, {})\n  {} ({}, {})".format (
                        cosphi, src_kw.name, src_kw.path, src_kw.linenumber, trg_kw.name, trg_kw.path, trg_kw.linenumber)
                    self.report (src_kw, msg, 0)
        msg = "W: High keyword body similarity ({} <= cosphi <= {}) count is {}".format (
            self.cosphi_low, self.cosphi_high, count)
        print (msg)
    """

    
