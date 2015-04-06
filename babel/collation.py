# -*- coding: utf-8 -*-
"""
    babel.collation
    ~~~~~~~~~~~~~

    Collation features based on the Unicode collation algorithm (UCA).

    :license: BSD, see LICENSE for more details.
"""

import os
import unicodedata

from babel._compat import pickle, cmp, range_type

_ducet_data = None

class Collation(object):

    def __init__(self, table):
        self.table = table


class Collator(object):
    
    def __init__(self, collation, normalization=True, strength=3,
        backward_levels=None):
        self.collation = collation
        self.normalization = normalization
        self.strength = strength
        self.backward_levels = backward_levels

    def compare(self, string1, string2):
        return cmp(self.key(string1), self.key(string2))

    def key(self, string):
        # Step 1. Produce a normalized form of each input string, applying S1.1.

        if self.normalization:
            string = unicodedata.normalize('NFD', string)

        # Step 2. The collation element array is built by sequencing through the
        # normalized form, applying S2.1 through S2.6.

        character_index = 0
        string_len = len(string)

        all_coll_elements = []

        while character_index < string_len:

            # S2.1 Find the longest initial substring S at each point that has a
            # match in the table.

            s_found = False
            s_plus_c_found = False

            for end in range_type(string_len, character_index, -1):
                s = string[character_index:end]

                if s in self.collation.table:
                    s_found = True
                    break

            # S2.1.1 If there are any non-starters following S, process each
            # non-starter C.

            c_chars = []
            for next_index in range_type(end, string_len -1):
                c = string[next_index:next_index + 1]
                cc_class = unicodedata.combining(c)
                if cc_class != 0:
                    c_chars.append((c, cc_class))
                else:
                    break

            if len(c_chars) > 1:

                # S2.1.2 If C is not blocked from S, find if S + C has a match
                # in the table.

                for c_char_index in range_type(1, len(c_chars)):
                    blocked = False
                    c_char = c_chars[c_char_index]
                    c = c_char[0]
                    cc_class = c_char[1]

                    # TODO: Check if blocked

                    if not blocked:

                        # S2.1.3 If there is a match, replace S by S + C, and
                        # remove C.

                        s_plus_c = s + c
                        if s_plus_c in self.collation.table:
                            s_plus_c_found = True
                            s = s_plus_c

                            c_index = end + c_char_index
                            string = string[:c_index] + string[c_index + 1:]

                            break

            # S2.2 Fetch the corresponding collation element(s) from the table
            # if there is a match. If there is no match, synthesize a weight as
            # described in Section 7.1, Derived Collation Elements.

            if s_found or s_plus_c_found:
                coll_elements = self.collation.table[s]

                character_index = end
            else:
                coll_elements = self.implicit_weight(s)

                character_index += 1

            # S2.3 Process collation elements according to the variable-weight
            # setting, as described in Section 3.6, Variable Weighting.

            # TODO: Implement Variable Weighting

            # S2.4 Append the collation element(s) to the collation element
            # array.

            for coll_element in coll_elements:
                all_coll_elements.append(coll_element[0])

        # Step 3. The sort key is formed by successively appending all non-zero
        # weights from the collation element array. The weights are appended
        # from each level in turn, from 1 to 3. (Backwards weights are inserted
        # in reverse order.)

        # S3.1 For each weight level L in the collation element array from 1 to
        # the maximum level,

        key = []

        coll_elements_len = map(lambda x: len(x), all_coll_elements)

        for level_index in range(max(self.strength, *coll_elements_len)):

            level = level_index + 1

            # S3.2 If L is not 1, append a level separator
            if level != 1:
                key.append(0)

            # S3.3 If the collation element table is forwards at level L,
            if (self.backward_levels is None or
                level not in self.backward_levels):

                # S3.4 For each collation element CE in the array
                for coll_element in all_coll_elements:

                    level_weight = coll_element[level_index]
                    #S3.5 Append CEL to the sort key if CEL is non-zero.
                    if level_weight != 0:
                        key.append(level_weight)

            else:
                # S3.6 Else the collation table is backwards at level L, so

                # S3.7 Form a list of all the non-zero CEL values.
                # S3.8 Reverse that list
                # S3.9 Append the CEL values from that list to the sort key.

                for coll_element in reversed(all_coll_elements):
                    level_weight = coll_element[level_index]
                    
                    if level_weight != 0:
                        key.append(level_weight)

        return key
    
    def implicit_weight(self, char):
        code_point = ord(char)

        base = 0xFBC0

        # Different base values for Han Unified Ideographs
        if 0x4E00 <= code_point <= 0x9FFF or 0xF900 <= code_point <= 0xFAFF:
            base = 0xFB40
        elif (0x3400 <= code_point <= 0x4DBF or
            0x20000 <= code_point <= 0x2A6DF or
            0x2A700 <= code_point <= 0x2B73F or
            0x2B740 <= code_point <= 0x2B81F):
            base = 0xFB80

        first_primary_weight = base + (code_point >> 15)
        second_primary_weight = (code_point & 0x7FFF) | 0x8000

        return [[[first_primary_weight, 0x0020, 0x0002], False],
            [[second_primary_weight, 0, 0], False]]


def _raise_no_data_error():
    raise RuntimeError('The babel data files are not available. '
                       'This usually happens because you are using '
                       'a source checkout from Babel and you did '
                       'not build the data files.  Just make sure '
                       'to run "python setup.py import_ducet" before '
                       'installing the library.')

def get_ducet():
    global _ducet_data
    if _ducet_data is None:
        dirname = os.path.join(os.path.dirname(__file__))
        filename = os.path.join(dirname, 'ducet.dat')
        if not os.path.isfile(filename):
            _raise_no_data_error()
        with open(filename, 'rb') as f:
            _ducet_data = pickle.load(f)
    return _ducet_data

def get_ducet_collation():
    return Collation(get_ducet()['table'])