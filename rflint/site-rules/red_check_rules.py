from rflint.common import TestRule, KeywordRule, GeneralRule, PostRule, ERROR, WARNING
from rflint.parser.rfkeyword import Keyword
from rflint.parser.testcase import Testcase

from numpy import finfo, argwhere, logical_and, nonzero, fill_diagonal, sort
import numpy
from sklearn.feature_extraction.text import TfidfVectorizer

import re

class PairwiseSimilarity (object):
    
    def find (self, cos_lower, cos_upper, doc_list):
        """Return the indices of similar documents
        """
        try:
            tfidf = TfidfVectorizer().fit_transform(doc_list)
            pwsim_array = (tfidf * tfidf.T).A
            pwsim_array = numpy.triu (pwsim_array, 1)
            cos_lower -= finfo("float64").eps
            cos_upper += finfo("float64").eps
            similars = argwhere (
                logical_and (pwsim_array >= cos_lower, cos_upper >= pwsim_array))
            sorted_similars = similars[similars[:,0].argsort()]
            return sorted_similars
        except ValueError as e:
            print ("Error in processing document collection: " + str(e))
            return numpy.array([])
    

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
    names and bodies.
    '''
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
    http://stackoverflow.com/questions/8897593/similarity-between-two-text-documents
    '''

    cosphi_low = 0.9
    cosphi_high = 1.0

    def configure (self, low, high):
        self.cosphi_low = float (low)
        self.cosphi_high = float (high)
    
    def apply (self, dummy):
        kw_names = [k.name for k in StoreKW.kw_list]
        pairs = PairwiseSimilarity().find(self.cosphi_low, self.cosphi_high, kw_names)
        old_filename_index = -1
        for pair in pairs:
            msg = self._format_msg (StoreKW.kw_list[pair[0]], StoreKW.kw_list[pair[1]])
            if pair[0] != old_filename_index:
                self.controller.set_print_filename(StoreKW.kw_list[pair[0]].path)
                old_filename_index = pair[0]
            self.report (StoreKW.kw_list[pair[0]], msg, StoreKW.kw_list[pair[0]].linenumber)
        msg = "W: High keyword name similarity ({} <= cosphi <= {}) count is {}".format (
            self.cosphi_low, self.cosphi_high, numpy.shape(pairs)[0])
        print (msg)
        
    def _format_msg (self, src_doc, trg_doc):
        msg = ("({}) resembles ({}, {}, {})".
               format (src_doc.name, trg_doc.name, trg_doc.path, trg_doc.linenumber))
        return msg


class KWRedundantBody (PostRule):
    '''Determine redundant resp. similar keyword and test implementations.
    
    Based on the assumption, that very similar keyword and test
    implementations might indicate duplicate or similar
    implementations (copies).

    Based on the approach described in:
    http://stackoverflow.com/questions/8897593/similarity-between-two-text-documents
    '''
    cosphi_low = 0.9
    cosphi_high = 1.0

    def configure (self, low, high):
        self.cosphi_low = float (low)
        self.cosphi_high = float (high)
    
    def apply (self, dummy):
        doc_list = StoreKW.kw_list + StoreTest.test_list
        kw_bodies = [" ".join ([r.raw_text for r in kw.rows]) for kw in doc_list]
        pairs = PairwiseSimilarity ().find (self.cosphi_low, self.cosphi_high, kw_bodies)
        old_filename_index = -1
        for pair in pairs:
            msg = self._format_msg (doc_list[pair[0]], doc_list[pair[1]])
            if pair[0] != old_filename_index:
                self.controller.set_print_filename(doc_list[pair[0]].path)
                old_filename_index = pair[0]
            self.report (doc_list[pair[0]], msg, doc_list[pair[0]].linenumber)
        msg = "W: Pairwise similarities ({} <= cosphi <= {}) count is {}".format (
            self.cosphi_low, self.cosphi_high, numpy.shape(pairs)[0])
        print (msg)
        
    def _format_msg (self, src_doc, trg_doc):
        msg = ("({}) body resembles ({}, {}, {})".
               format (src_doc.name, trg_doc.name, trg_doc.path, trg_doc.linenumber))
        return msg

