#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    import_ducet
    ~~~~~~~~~~~~

    Script that import the Default Unicode Collation Element Table (DUCET) and
    dumps a pickled version of it in the project. The DUCET can be found on
    http://www.unicode.org/Public/UCA/ .

    :license: BSD, see LICENSE for more details.
"""
from optparse import OptionParser
import os
import sys

# Make sure we're using Babel source, and not some previously installed version
sys.path.insert(0, os.path.join(os.path.dirname(sys.argv[0]), '..'))

from babel._compat import pickle, unichr

def main():
    parser = OptionParser(usage='%prog path/to/allkeys.txt')
    options, args = parser.parse_args()
    if len(args) != 1:
        parser.error('incorrect number of arguments')

    allkeys_path = args[0]
    destdir = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
        '..', 'babel')

    ducet_path = os.path.join(destdir, 'ducet.dat')
    ducet_table = {}
    ducet = {
        'table': ducet_table,
        'version': None
    }

    with open(allkeys_path, mode='rb') as f:
        for line in f:
            line = line.split(b'#')[0].split(b'%')[0].strip()
            if not line:
                continue

            if line.startswith(b'@version'):
                ducet['version'] = line.split(b' ')[1]
            else:
                char_list, coll_elements = line.split(b';')
                char_list = char_list.strip()
                coll_elements = coll_elements.strip()

                uni_chars = []
                for char in char_list.split(b' '):
                    if not char:
                        continue
                    uni_chars.append(unichr(int(char, 16)))

                uni_chars = u''.join(uni_chars)

                colls = []
                for coll_element in coll_elements.split(b'['):
                    coll_element = coll_element.strip()
                    if not coll_element:
                        continue

                    if not coll_element.endswith(b']'):
                        continue

                    coll_element = coll_element[:-1]

                    variable = coll_element.startswith(b'*')

                    coll_element = coll_element[1:]

                    weights = []
                    for weight in coll_element.split(b'.'):
                        weights.append(int(weight, 16))

                    colls.append([weights, variable])

                ducet_table[uni_chars] = colls

    with open(ducet_path, 'wb') as f:
        pickle.dump(ducet, f, 2)


if __name__ == '__main__':
    main()