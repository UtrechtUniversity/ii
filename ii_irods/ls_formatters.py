"""This files contains formatters for the output formats of the ls command"""
import csv
from datetime import datetime
import json
import yaml
import sys

from columnar import columnar
from humanize import naturalsize

from ii_irods.utils import print_warning


class ListFormatter(object):

    def print_data(self, data, args):
        raise NotImplementedError

    def _readable_date(self, date, args):
        return datetime.fromtimestamp(date).strftime('%Y-%m-%d %H:%M')

    def _readable_size(self, size, args):
        if args["hrsize"] == "yes" or args["hrsize"] == "default":
            return naturalsize(size, gnu=True)
        else:
            return size

    def _readable_repl_status(self, status):
        if status == "1":
            return "OK"
        else:
            return "STL"

    def _collapse_results(self, queries):
        results = []
        for query in queries:
            if "results" in query:
                results.extend(query["results"])
        return results

    def _top_of_collection(self, collection):
        return collection.split("/")[-1]


class TextListFormatter(ListFormatter):
    """Formatter for plain (non-coloured) text, similar to the
    output of ils."""

    def print_data(self, data, args):
        """TODO"""
        if args["l"]:
            self._print_data_long(data, args, False)
        elif args["L"]:
            self._print_data_long(data, args, True)
        else:
            self._print_data_default(data, args)

    def _print_data_long(self, data, args, print_phy_path=False):
        for query in data:
            querytype = query["expanded_query_type"]
            expanded_query = query["expanded_query"]
            original_query = query["original_query"]
            if querytype == "collection":
                print("{}:".format(expanded_query))
                results = query["results"]
                if len(results) == 0:
                    print()
                    continue
                tdata = []
                for result in results:
                    if result["type"] == "collection":
                        tdata.append(["C",
                                      result["owner_name"],
                                      "-",
                                      "-",
                                      "-",
                                      "-",
                                      self._readable_date(
                                          result["modify_time"], args),
                                      self._top_of_collection(result["name"])])
                    elif result["type"] == "dataobject":
                        tdata.append(["D",
                                      result["owner_name"],
                                      result["replica_number"],
                                      result["resc_name"],
                                      self._readable_repl_status(
                                          result["replica_status"]),
                                      self._readable_size(
                                          result["size"], args),
                                      self._readable_date(
                                          result["modify_time"], args),
                                      result["name"]])
                        if print_phy_path:
                            tdata.append(["", "", "", "", "", "", "PHY PATH:",
                                          result["physical_path"]])
                self._print_table_l(tdata, args)
            elif querytype == "dataobject":
                results = query["results"]
                tdata = []
                for result in results:
                    tdata.append(["D",
                                  result["owner_name"],
                                  result["replica_number"],
                                  result["resc_name"],
                                  self._readable_repl_status(
                                      result["replica_status"]),
                                  self._readable_size(result["size"], args),
                                  self._readable_date(
                                      result["modify_time"], args),
                                  result["name"]])
                    if print_phy_path:
                        tdata.append(["", "", "", "", "", "", "PHY PATH:",
                                      result["physical_path"]])
                self._print_table_l(tdata, args)
            else:
                print_warning(
                    "Unexpected query type {} in text formatter".format(querytype))

    def _print_table_l(self, data, args, print_headers=True):
        justify = ["l", "l", "l", "l", "l", "r", "l", "l"]
        if print_headers:
            headers = [
                "Type",
                "Owner",
                "R#",
                "Resource",
                "R?",
                "Size",
                "Mdate",
                "name"]
            table = columnar(
                data,
                headers=headers,
                justify=justify,
                no_borders=True)
        else:
            table = columnar(data, justify=justify, no_borders=True)

        print(table)

    def _print_data_default(self, data, args):
        for query in data:
            querytype = query["expanded_query_type"]
            expanded_query = query["expanded_query"]
            original_query = query["original_query"]
            if querytype == "collection":
                print("{}:".format(expanded_query))
                results = query["results"]
                for result in results:
                    if result["type"] == "collection":
                        print("C " + result["name"])
                    elif result["type"] == "dataobject":
                        print("D " + result["name"])
                print()
            elif querytype == "dataobject":
                print("D " + original_query)
            else:
                print_warning(
                    "Unexpected query type {} in text formatter".format(querytype))


class CSVListFormatter(ListFormatter):
    """Formatter for output in comma-separated values (CSV) format"""

    def _readable_size(self, size, args):
        if args["hrsize"] == "yes":
            return naturalsize(size, gnu=True)
        else:
            return size

    def print_data(self, data, args):
        w = csv.writer(sys.stdout)
        w.writerow(["Type", "Original query", "Owner name", "Replica number",
                    "Resource name", "Replica status", "Size",
                    "Modification time", "Name", "Full name", "Physical path"])
        for query in data:
            querytype = query["expanded_query_type"]
            expanded_query = query["expanded_query"]
            original_query = query["original_query"]
            if querytype == "collection":
                results = query["results"]
                if len(results) == 0:
                    print()
                    continue
                for result in results:
                    if result["type"] == "collection":
                        w.writerow(["collection",
                                    original_query,
                                    result["owner_name"],
                                    "-",
                                    "-",
                                    "-",
                                    "-",
                                    self._readable_date(
                                        result["modify_time"], args),
                                    self._top_of_collection(
                                        result["name"]),
                                    result["name"],
                                    "-"])
                    elif result["type"] == "dataobject":
                        w.writerow(["dataobject",
                                    original_query,
                                    result["owner_name"],
                                    result["replica_number"],
                                    result["resc_name"],
                                    self._readable_repl_status(
                                        result["replica_status"]),
                                    self._readable_size(result["size"], args),
                                    self._readable_date(
                                        result["modify_time"], args),
                                    result["name"],
                                    result["full_name"],
                                    result["physical_path"]])
            elif querytype == "dataobject":
                results = query["results"]
                for result in results:
                    w.writerow([
                        "dataobject",
                        original_query,
                        result["owner_name"],
                        result["replica_number"],
                        result["resc_name"],
                        self._readable_repl_status(result["replica_status"]),
                        self._readable_size(result["size"], args),
                        self._readable_date(result["modify_time"], args),
                        result["name"],
                        result["full_name"],
                        result["physical_path"]])
            else:
                print_warning(
                    "Unexpected query type {} in text formatter".format(querytype))


class JSONListFormatter(ListFormatter):
    """Formatter for output in JSON format"""

    def print_data(self, data, args):
        resultdata = self._collapse_results(data)
        print(json.dumps(resultdata, indent=4, sort_keys=True))


class YAMLListFormatter(ListFormatter):
    """Formatter for output in JSON format"""

    def print_data(self, data, args):

        resultdata = self._collapse_results(data)
        print(yaml.dump(resultdata))
