'''
Author: Hao-Ting Wang
Date: 23-01-2021

Generate Markdown table from csv / tsv file and
append to an existing markdown file containing
page header and other free text paragraph for
acknowledgements and contributors page.

Usage:
>> python brainhack_book/mdtable.py acknowledgements
>> python brainhack_book/mdtable.py contributors
'''
import os
import sys
from pathlib import Path
import csv


div_h = "-"
div_v = "|"
padding = 2

class MarkdownTable():
    '''
    Generate markdown table from csv/tsv file,
    append to an existing markdown file.

    inputs
    ------
    table:
        table loaded through csv.reader
        Each row is a list and have the same lenght
        e.g.:
        table = [["a", "b", "c"],
            ["d", "e", "f"],
            ["g", "i", "j"]]

    descriptions:
        List of string where each item is a line
    '''
    def __init__(self, table, descriptions):
        self.table = table
        self.descriptions = descriptions

    def generate(self):
        """
        generate markdown file with a table
        save as a .md file
        """
        header = self.table [0]
        body = self.table [1:]

        # add dividers
        horiz = self.header_div(header)
        header = self.add_div(header)
        body = [self.add_div(row) for row in body]
        # write the table
        mdtable = self.assemble_table(self.descriptions,
            header, horiz, body)
        return self.write_md(mdtable)

    @staticmethod
    def add_div(line):
        '''
        add markdown table divider to a row
        '''
        div = ''.join([padding * ' ', div_v, padding * ' '])
        return div.join(line)

    @staticmethod
    def header_div(header):
        '''
        add markdown table horizontal divider bellow header
        '''
        col_widths = [len(cell) for cell in header]
        horizs = ["-" * w for w in col_widths]
        div = ''.join([padding * div_h, div_v, padding * div_h])
        return div.join(horizs)

    @staticmethod
    def assemble_table(title_part, header, horiz, body):
        '''
        assemble header, devider and table body as
        a markdown table
        prepend with exisiting .md file
        '''
        table = title_part + [header, horiz, *body]
        return [row.rstrip() for row in table]

    @staticmethod
    def write_md(table):
        '''
        write output from `assemble_table` to a string
        suitable for writing a .md file
        '''
        return '\n'.join(table)

def drop_author_column(data, header, keyword):
    '''
    lazy drop column with a certain keyword
    '''
    trimmed = data.copy()
    source_header = header.copy()

    # remove the consent column the lazy way
    idx_consent = [i for i, c in enumerate(source_header) if keyword in c][0]
    for l in trimmed:
        l.pop(idx_consent)
    return trimmed

def parse_affiliation(data):
    '''
    A very lazy affiliation table trimmer
    collaspe name
    trimm off url part of ORCID
    email hyperlink to name
    '''
    trimmed = [l[9:] for l in data[1:]]  # lazy attempt to remove irrelavant cells

    for kw in ["Email", "psyarxiv"]:
        source_header = trimmed[1].copy()
        trimmed = drop_author_column(trimmed, source_header, kw)

    orig_top, orig_header, orig_body = trimmed[0], trimmed[1], trimmed[2:]

    # rename top level header
    idx = {h: i for i, h in enumerate(orig_header)}  # header to index translator

    header = ["Name", "Affiliation"]
    idx_first_aff = idx[
        "Affiliation (please use the format: Department / Institution / City / Country)"
        ]

    # having three place holder is a hack; my table generator has problem with empty cells
    # when len(shorten_top) == len(body[0]),
    # table cut off the final column, top level not in line with the header in markdown
    # not sure why this fix the issue
    shorten_top = ["", "", ""] + orig_top[(idx_first_aff + 3):] + ["", "", ""]
    # manually relable the top level headers
    new_names = ["Tasks performed", "Manuscript section contribution"]
    top_level = [new_names.pop(0) if c != "" else " " for c in shorten_top]

    header += orig_header[(idx_first_aff + 3):]
    parsed = [top_level, header]
    for line in orig_body:
        body = []
        name = parse_name(line, idx)
        body.append(name)

        body.append(line[idx_first_aff])
        body += line[(idx_first_aff + 3):]
        parsed.append(body)
    return parsed

def parse_name(line, idx):
    if not line[idx["Middle initial(s)"]]:
         return " ".join([line[idx["First name"]],
         line[idx["Last name"]]])
    init = line[idx["Middle initial(s)"]][0] + "."
    return " ".join([line[idx["First name"]],
        init, line[idx["Last name"]]])

def read_tablefile(filename, delimiter="\t"):
    '''
    Read tsv or csv
    '''
    if delimiter not in [",", "\t"]:
        print(f"unsupported delimiter `{delimiter}`")
        return

    with open(filename, "r") as f:
        csv_reader = csv.reader(f, delimiter=delimiter)
        return list(csv_reader)

def read_page_descriptions(filename):
    '''
    Read the header and addtional text from a markdown file.
    Return a list of string, one item per line
    Line breakers were stripped to fit MarkdownTable.assemble_table

    e.g. ["# header", "Some content."]
    '''
    with open(filename, "r") as f:
        return [l.split("\n")[0] for l in f.readlines()]

def write_page(filename, md):
    '''
    write markdown file

    filename:
        path to book dir and file name

    md:
        output from MarkdownTable.generate
    '''
    with open(filename, "w") as f:
        f.write(md)

def build_acknowledgement(project_root):
    ack_path = project_root / "data" / "acknowledgements.csv"
    ack_desc_path = project_root / "data" / "acknowledgements_descriptions.md"
    ack_page = project_root / "brainhack_book" / "acknowledgements.md"

    table = read_tablefile(ack_path, delimiter=",")
    desc = read_page_descriptions(ack_desc_path)

    mder = MarkdownTable(table, desc)
    md = mder.generate()
    write_page(ack_page, md)


def fetch_osf(osf_path, local_path, projectid="4szct"):
    """
    lazy wrapper to fetch osf spreadsheet
    """
    filename = Path(osf_path).name
    os.system(f"osf -p {projectid} fetch {osf_path} {local_path}")
    print(f"fetch {osf_path}, save to {local_path}")

def build_contributors(project_root):
    aff_path = project_root / "data" / \
        "contributors.tsv"
    contributions_desc_path = project_root / "data" / "contributors_descriptions.md"
    contributions_page = project_root / "brainhack_book" / \
        "contributors.md"
    aff = read_tablefile(aff_path, delimiter="\t")
    desc = read_page_descriptions(contributions_desc_path)
    aff = parse_affiliation(aff)

    mder = MarkdownTable(aff, desc)
    md = mder.generate()
    write_page(contributions_page, md)

if __name__ == '__main__':
    project_root = Path(__file__).parents[1]
    if len(sys.argv) == 2:
        if sys.argv[1] == "acknowledgements":
            # create acknowledgements page
            build_acknowledgement(project_root)
        elif sys.argv[1] == "contributors":
            # osf_path = "affiliation_and_consent_for_the_brainhack_neuroview_preprint_source.tsv"
            # local_path = "data/contributors.tsv"
            # fetch_osf(osf_path, local_path, projectid="4szct")
            build_contributors(project_root)
        else:
            print("unsupported input")
    else:
        print("require input: acknowledgements or contributors")