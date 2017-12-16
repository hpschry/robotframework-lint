"""
Redundancy check rules for rflint

Keyword name similarity detection, 
Test body and keyword body similarity detection

Copyright 2017 Hans-Peter Schreiter

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

"""
import logging
import re

from numpy import finfo, argwhere, logical_and, nonzero, fill_diagonal, sort
import numpy
from sklearn.feature_extraction.text import TfidfVectorizer

from rflint.common import Rule, TestRule, KeywordRule, GeneralRule, PostRule, ERROR, WARNING
from rflint.parser.rfkeyword import Keyword
from rflint.parser.testcase import Testcase


class PairwiseSimilarityRule(Rule):
    """Implement methods to find pairs of matching documents.

    Based on the approach described in:
    http://stackoverflow.com/questions/8897593/similarity-between-two-text-documents

    Also this class implements a reporting method to report pairs of
    similar documents.

    This class needs to be derived from Rule, otherwise it does not
    get initialized.

    """

    old_doc_ref = ""

    def __init__(self, controller, severity=None):
        # self.old_doc_ref = ""
        super (PairwiseSimilarityRule, self).__init__(controller, severity)
    
    def find_pairs(self, cos_lower, cos_upper, doc_list):
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
            # If the match algorithm is called on an empty document
            # collection, e.g. in case of empty input files, it throws
            # an exception that is reported on stderr, but does not
            # terminate execution.
            logging.warning("Error in processing document collection: " + str(e))
            return numpy.array([])

    def report_pair(self, doc_ref, obj, message, linenum, char_offset=0):
        """Report similar documents.
        
        Sets the filename in the controller.
        """
        if PairwiseSimilarityRule.old_doc_ref != doc_ref:
            self.controller.set_print_filename(doc_ref)
            PairwiseSimilarityRule.old_doc_ref = doc_ref
        self.report(obj, message, linenum, char_offset)


class StoreTest (TestRule):
    """Pseudo rule to store all test information in a list."""
    
    test_list = []

    def apply (self, testcase):
        self.test_list.append (testcase)
        

class StoreKW (KeywordRule):
    '''Pseudo rule to store all keyword information in a list.

    Put the keyword objects in a list while they are traversed.
    This is for later processing (finding similar keyword 
    names and bodies.
    '''
    kw_list = []

    def apply (self, keyword):
        self.kw_list.append (keyword)


class DummyObject(object):
    path=""


class KWRedundantName (PostRule, PairwiseSimilarityRule):
    '''Determine redundant resp. similar keyword names.
    
    Based on the assumption, that very similar keyword names
    might indicate duplicate or similar implementations.

    Note: it might make sense to set the upper threshold (high) to a
    value slightly smaller than 1.0 to exclude similarities that were
    created by intent (e.g. multiple setup suite implementations).

    '''

    cosphi_low = 0.95
    cosphi_high = 1.0

    def __init__(self, controller, severity=WARNING):
        super (KWRedundantName, self).__init__(controller, severity)

    def configure (self, low, high):
        self.cosphi_low = float (low)
        self.cosphi_high = float (high)
    
    def apply (self, dummy):
        kw_names = [k.name for k in StoreKW.kw_list]
        pairs = self.find_pairs(self.cosphi_low, self.cosphi_high, kw_names)
        for pair in pairs:
            src_doc = StoreKW.kw_list[pair[0]]
            trg_doc = StoreKW.kw_list[pair[1]]
            msg = ("({}) resembles ({}, {}, {})".
                   format(src_doc.name, trg_doc.name, trg_doc.path,
                          trg_doc.linenumber))
            self.report_pair(src_doc.path, src_doc, msg, src_doc.linenumber)
        if numpy.shape(pairs)[0] > 0:
            msg = "High keyword name similarity ({} <= cosphi <= {}) count is {}".format(
                self.cosphi_low, self.cosphi_high, numpy.shape(pairs)[0])
            # print (msg)
            self.report(DummyObject(), msg, 0, 0)
        

class KWRedundantBody (PostRule, PairwiseSimilarityRule):
    '''Determine redundant resp. similar keyword and test implementations.

    Based on the assumption, that very similar keyword and test
    implementations might indicate duplicate or similar
    implementations (copies).

    '''
    cosphi_low = 0.95
    cosphi_high = 1.0

    def __init__(self, controller, severity=None):
        super(KWRedundantBody, self).__init__(controller, severity)

    def configure (self, low, high):
        self.cosphi_low = float (low)
        self.cosphi_high = float (high)
    
    def apply (self, dummy):
        doc_list = StoreKW.kw_list + StoreTest.test_list
        kw_bodies = [" ".join ([r.raw_text for r in kw.rows]) for kw
                     in doc_list]
        pairs = self.find_pairs(self.cosphi_low, self.cosphi_high, kw_bodies)
        for pair in pairs:
            src_doc = doc_list[pair[0]]
            trg_doc = doc_list[pair[1]]
            msg = ("({}) body resembles ({}, {}, {})".
                   format(src_doc.name, trg_doc.name, trg_doc.path,
                          trg_doc.linenumber))
            self.report_pair(src_doc.path, src_doc, msg, src_doc.linenumber)
        if numpy.shape(pairs)[0] > 0:
            msg = "Pairwise similarities ({} <= cosphi <= {}) count is {}".format(
                self.cosphi_low, self.cosphi_high, numpy.shape(pairs)[0])
            self.report(DummyObject(), msg, 0, 0)
        
