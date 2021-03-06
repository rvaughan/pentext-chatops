#!/usr/bin/env python

"""
Builds PDF files from (intermediate fo and) XML files.

This script is part of the PenText framework
                           https://pentext.org

   Copyright (C) 2015-2016 Radically Open Security
                           https://www.radicallyopensecurity.com

                Author(s): Peter Mosmans

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

"""

from __future__ import absolute_import
from __future__ import print_function

import argparse
import os
import random
import subprocess
from subprocess import PIPE
import sys
import textwrap
from ros.logger import (
    debug,
    rc_log,
)

GITREV = 'GITREV'  # Magic tag which gets replaced by the git short commit hash
OFFERTE = 'generate_offerte.xsl'  # XSL for generating waivers
WAIVER = 'waiver_'  # prefix for waivers
EXECSUMMARY = 'execsummary'  # generating an executive summary instead of a report


def parse_arguments():
    """
    Parses command line arguments.
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent('''\
Builds PDF files from (intermediate fo and) XML files.

Copyright (C) 2015-2017  Radically Open Security (Peter Mosmans)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.'''))
    parser.add_argument('-c', '--clobber', action='store_true',
                        help='overwrite output file if it already exists')
    parser.add_argument('-date', action='store',
                        help='the invoice date')
    parser.add_argument('--execsummary', action='store_true',
                        help="""create an executive summary as well as a report (true/false).
                        Default: false """)
    parser.add_argument('--nopw', action='store_true',
                        help="""password-protect the pdf.
                        Default: false """)
    parser.add_argument('--fop-config', action='store',
                        default='/etc/docbuilder/fop.xconf',
                        help="""fop configuration file (default
                        /etc/docbuilder/fop.xconf""")
    parser.add_argument('-f', '--fop', action='store',
                        default='../target/report.fo',
                        help="""intermediate fop output file (default:
                        ../target/report.fo)""")
    parser.add_argument('--fop-binary', action='store',
                        default='/usr/local/bin/fop',
                        help='fop binary (default /usr/local/bin/fop')
    parser.add_argument('-i', '--input', action='store',
                        default='report.xml',
                        help="""input file (default: report.xml)""")
    parser.add_argument('-invoice', action='store',
                        help="""invoice number""")
    parser.add_argument('--saxon', action='store',
                        default='/usr/local/bin/saxon/saxon9he.jar',
                        help="""saxon JAR file (default
                        /usr/local/bin/saxon/saxon9he.jar)""")
    parser.add_argument('-x', '--xslt', action='store',
                        default='../xslt/generate_report.xsl',
                        help='input file (default: ../xslt/generate_report.xsl)')
    parser.add_argument('-o', '--output', action='store',
                        default='../target/report-latest.pdf',
                        help="""output file name (default:
                        ../target/report-latest.pdf""")
    parser.add_argument('--tag', action='store_true',
                        help="""Modify GITREV with git commit hash""")
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='increase output verbosity')
    parser.add_argument('-w', '--warnings', action='store_true',
                        help='show warnings')
    args = parser.parse_args()

    return vars(args)


def print_output(stdout, stderr):
    """
    Prints out standard out and standard err using the verboseprint function.
    """
    if stdout:
        debug('[+] stdout: {0}'.format(stdout))  # noqa F821
    if stderr:
        debug('[-] stderr: {0}'.format(stderr))  # noqa F821


def change_tag(fop):
    """
    Replaces GITREV in document by git commit shorttag.
    """
    cmd = ['git', 'log', '--pretty=format:%h', '-n', '1']
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        shorttag, _stderr = process.communicate()
        if not process.returncode:
            fop_file = open(fop).read()
            if GITREV in fop_file:
                fop_file = fop_file.replace(GITREV, shorttag)
                with open(fop, 'w') as new_file:
                    new_file.write(fop_file)
                print('[+] Embedding git version information into document')
    except OSError:
        print('[-] could not execute git - is git installed ?')


def generate_pw():
    s = "abcdefghijklmnopqrstuvwxyz01234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()?"
    length = 12
    p = "".join(random.sample(s, length))
    return(p)


def to_fo(options):
    """
    Creates a fo output file based on a XML file.
    Returns True if successful
    """
    cmd = ['java', '-jar', options['saxon'],
           '-s:' + options['input'], '-xsl:' + options['xslt'],
           '-o:' + options['fop'], '-xi']
    if options['invoice']:
        cmd.append('INVOICE_NO=' + options['invoice'])
    if options['date']:
        cmd.append('DATE=' + options['date'])
    if options['execsummary']:
        cmd.append('EXEC_SUMMARY=true')
    process = subprocess.Popen(cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    print_output(stdout, stderr)
    if options['verbose']:
        rc_log(stdout)
        rc_log(stderr)
    if process.returncode:
        print_exit('[-] Error creating fo file from XML input',
                   process.returncode)
    else:
        if options['tag']:
            change_tag(options['fop'])
    return True


def to_pdf(options):
    """
    Creates a PDF file based on a fo file.
    Returns True if successful
    """
    cmd = [options['fop_binary'], '-c', options['fop_config'], options['fop'],
           options['output']]
    if not options['nopw']:
        pw = generate_pw()
        cmd = cmd + ['-u', pw]
    if options['verbose']:
        cmd = cmd + ['-v']
    try:
        debug('Converting {0} to {1}'.format(options['fop'],  # noqa F821
                                                    options['output']))
        process = subprocess.Popen(cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        result = process.returncode
        print_output(stdout, stderr)
        if options['verbose']:
            rc_log(stdout)
            rc_log(stderr)
        if result == 0:
            print('[+] Succesfully built ' + options['output'])
            if not options['nopw']:
                print('\n[+] Password for this pdf is ' + pw)
    except OSError as exception:
        print_exit('[-] ERR: {0}'.format(exception.strerror), exception.errno)
    return result == 0


def print_exit(text, result):
    """
    Prints error message and exits with result code.
    """
    print(text, file=sys.stderr)
    sys.exit(result)


def main():
    """
    The main program.
    """
    result = False
    options = parse_arguments()
    if not os.path.isfile(options['input']):
        print_exit('[-] Cannot find input file {0}'.
                   format(options['input']), result)
    try:
        if os.path.isfile(options['output']):
            if not options['clobber']:
                print_exit('[-] Output file {0} already exists. '.
                           format(options['output']) +
                           'Use -c (clobber) to overwrite',
                           result)
            os.remove(options['output'])
    except OSError as exception:
        print_exit('[-] Could not remove/overwrite file {0} ({1})'.
                   format(options['output'], exception.strerror), result)
    result = to_fo(options)
    if result:
        if OFFERTE in options['xslt']:  # an offerte can generate multiple fo's
            report_output = options['output']
            debug('generating separate waivers detected')  # noqa F821
            output_dir = os.path.dirname(options['output'])
            fop_dir = os.path.dirname(options['fop'])
            try:
                for fop in [os.path.splitext(x)[0] for x in
                            os.listdir(fop_dir) if x.endswith('fo')]:
                    if WAIVER in fop:
                        options['output'] = output_dir + os.sep + fop + '.pdf'
                    else:
                        options['output'] = report_output
                    options['fop'] = fop_dir + os.sep + fop + '.fo'
                    result = to_pdf(options) and result
            except OSError as exception:
                print_exit('[-] ERR: {0}'.format(exception.strerror),
                           exception.errno)
        if options['execsummary'] is True:  # we're generating a summary as well as a report
            report_output = options['output']
            debug('generating additional executive summary')
            output_dir = os.path.dirname(options['output'])
            fop_dir = os.path.dirname(options['fop'])
            try:
                for fop in [os.path.splitext(x)[0] for x in
                            os.listdir(fop_dir) if x.endswith('fo')]:
                    if EXECSUMMARY in fop:
                        options['output'] = output_dir + os.sep + fop + '.pdf'
                    else:
                        options['output'] = report_output
                    options['fop'] = fop_dir + os.sep + fop + '.fo'
                    result = to_pdf(options) and result
            except OSError as exception:
                print_exit('[-] ERR: {0}'.format(exception.strerror),
                           exception.errno)
        else:
            result = to_pdf(options)

    else:
        print_exit('[-] Unsuccessful (error {0})'.format(result), result)
    sys.exit(not result)


if __name__ == "__main__":
    main()
