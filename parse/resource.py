import argparse
import os
import json
import subprocess


class ArgumentParser(argparse.ArgumentParser):
    def __init__(self):
        desc = "Parses data from persistent resources during an upgrade"
        usage_string = "resource-parse [-u/--upgrade-rie] "

        super(ArgumentParser, self).__init__(
            usage=usage_string, description=desc)

        self.add_argument(
            "-u", "--upgrade-dir", metavar="", required=True,
            default=None, help="The path to the upgrade test directory.")


def parse_data(sub_file, _file):

    name, _ = _file.split(".")
    output = open(sub_file).read().splitlines()[1:]

    results = {}

    # if multiple lines in file
    for line in output:
        test_name, status, start, stop = line.split(",")

        # if test fail during setup
        if "setUpClass" in test_name:
            _, action, product = test_name.split("(")[1].split(".")[-2].split("_", 2)
            test = "test_" + action + "_" + product
        else:
            test = test_name.split("[")[0].split(".")[-1]
            _, action, product = test_name.split("[")[0].split(".")[-3].split("_", 2)

        if "object" in product:
            product = product[:-10]

        # add key to dict
        if product not in results:
            results[product] = {}

        if action not in results[product]:
            if action == "validate":
                if "upgrade" in name:
                    action = name.split("_")[0] + "-" + action
            results[product].setdefault(action, [])

        values = {
                "test_name": test,
                "task": action,
                action: True if status == "success" else False,
                "start": start,
                "stop": stop,
                "service": product
            }

        results[product][action].append(values)

    return results


def convert_file(path_dir):
    for _file in os.listdir(path_dir):
        command = "cat " + _file + "|subunit-1to2|subunit2csv > " + _file + ".csv"
        action = subprocess.Popen(command, shell=True, stdout=None)
        action.wait()


def parse(path_dir):
    data = {}

    convert_file(path_dir)

    for _file in os.listdir(path_dir):

        if _file.endswith(".csv"):
            call = parse_data(os.path.join(path_dir, _file), _file)

            # iterate over keys in returned
            for key, value in call.items():
                if key not in data:
                    data[key] = {}
                data[key].update(value)

    return json.dumps(data)


def entry_point():
    cls_args = ArgumentParser().parse_args()
    print parse(cls_args.upgrade_dir)
