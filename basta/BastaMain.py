#!/usr/bin/env python

import sys
import os
import logging
import plyvel
import argparse
from subprocess import call

# Quick'n'Dirty! Change!
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from basta import FileUtils as futils
from basta import TaxTree as ttree
from basta import AssignTaxonomy
from basta import DownloadUtils as dutils
from basta import DBUtils as dbutils
from basta import NCBITaxonomyCreator as ntc 


############
#
#   Main class to start all basta related functions
#
####
#   COPYRIGHT DISCALIMER:
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
#
#   Author: Tim Kahlke, tim.kahlke@audiotax.is
#   Date:   April 2017
#



class Main():

    def __init__(self):
        logging.basicConfig(format='',level=logging.INFO)
        self.logger = logging.getLogger()
        

    def run_basta(self,args):
        if args.subparser_name == 'sequence':
            self._basta_sequence(args)
        elif args.subparser_name == 'single':
            self._basta_single(args)
        elif args.subparser_name == 'multiple':
            self._basta_multiple(args)
        elif args.subparser_name == 'download':
            self._basta_download(args)
        elif args.subparser_name == 'create_db':
            self._basta_create_db(args)
        elif args.subparser_name == 'taxonomy':
            self._basta_taxonomy(args)


    def _basta_sequence(self,args):
        self.logger.info("\n#### Assigning taxonomy to each sequence ###\n")
        (map_file, db_file) = self._get_db_name(args.type)
        assigner = AssignTaxonomy.Assigner(args.evalue,args.alen,args.identity,args.number,args.minimum,args.lazy,args.tax_method,args.directory)
        assigner._assign_sequence(args.blast,args.output,db_file)
        self.logger.info("\n#### Done. Output written to %s" % (args.output))


    def _basta_single(self,args):
        self.logger.info("\n#### Assigning one taxonomy based on all sequences ###\n")
        (map_file, db_file) = self._get_db_name(args.type)
        assigner = AssignTaxonomy.Assigner(args.evalue,args.alen,args.identity,args.number,args.minimum,args.lazy,args.tax_method,args.directory) 
        lca = assigner._assign_single(args.blast,db_file)
        self.logger.info("\n##### Results ("+ args.tax_method +")#####\n")
        self.logger.info("Last Common Ancestor: %s\n" % (lca))
        self.logger.info("\n###################\n")

        
    def _basta_multiple(self,args):
        self.logger.info("\n####  Assigning one taxonomy for each file ###\n")
        (map_file, db_file) = self._get_db_name(args.type)
        assigner = AssignTaxonomy.Assigner(args.evalue,args.alen,args.identity,args.number,args.minimum,args.lazy,args.tax_method,args.directory)
        assigner._assign_multiple(args.blast,args.output,db_file)
        self.logger.info("\n###### Done. Output written to %s" % (args.output))


    def _get_db_name(self,db_type):
        if db_type == "prot":
            return ("prot.accession2taxid.gz", "prot_mapping.db")
        elif db_type == "wgs":
            return ("nucl_wgs.accession2taxid.gz", "wgs_mapping.db")
        elif db_type == "gss":
            return ("nucl_gss.accession2taxid.gz", "gss_mapping.db")
        elif db_type == "est":
            return ("nucl_est.accession2taxid.gz", "est_mapping.db")
        elif db_type == "pdb":
            return ("pdb.accession2taxid.gz", "pdb_mapping.db")
        else:
            return ("nucl_gb.accession2taxid.gz", "gb_mapping.db")


    def _basta_download(self,args):
        self.logger.info("\n# 1. Download mapping file(s) from NCBI ###\n")
        (map_file, db_file) = self._get_db_name(args.type)
        if args.type == "prot":
            map_file = "prot.accession2taxid.gz"
            db_file = "prot_mapping.db"
        elif args.type == "wgs":
            map_file = "nucl_wgs.accession2taxid.gz"
            db_file = "wgs_mapping.db"
        elif args.type == "gss":
            map_file = "nucl_gss.accession2taxid.gz"
            db_file = "gss_mapping.db"
        elif args.type == "est":
            map_file = "nucl_est.accession2taxid.gz"
            db_file = "est_mapping.db"
        elif args.type == "pdb":
            map_file = "pdb.accession2taxid.gz"
            db_file = "pdb_mapping.db"
        else:
            map_file = "nucl_gb.accession2taxid.gz"
            db_file = "gb_mapping.db"

        dutils.down_and_check(args.ftp,map_file,args.mapping_dir)
        self.logger.info("\n# 2. Creating mapping database\n")
        dbutils.create_db(args.mapping_dir,map_file,db_file,0,2)
        self.logger.info("\n# Done. Downloaded and processed file %s\n" % (map_file))


    def _basta_create_db(self,args):
        self.logger.info("\n#### Creating database\n")
        dbutils.create_db(args.database_dir,args.input,args.output,args.key,args.value)
        self.logger.info("\n#### Done. Processed file %s\n" % (args.input))


    def _basta_taxonomy(self,args):
        self.logger.info("\n#### Downloading and processing NCBI taxonomy files\n")
        self.logger.info("# 1. Download taxonomy files")
        dutils.down_and_check("ftp://ftp.ncbi.nih.gov/pub/taxonomy/","taxdump.tar.gz",args.output)
        call(["tar", "-xzvf", os.path.join(args.output,"taxdump.tar.gz"), "-C", args.output])

        self.logger.info("\n# 2. Creating complete taxonomy file\n")
        tax_creator = ntc.Creator(os.path.join(args.output,"names.dmp"),os.path.join(args.output,"nodes.dmp"))
        tax_creator._write(os.path.join(args.output,"complete_taxa"))

        self.logger.info("# 3. Creating taxonomy database")
        dbutils.create_db(args.output,"complete_taxa.gz","complete_taxa.db",0,1)
