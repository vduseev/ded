#!/usr/bin/env python3

import sys
import argparse

from ruamel.yaml import YAML


def _parse():
    parser = argparse.ArgumentParser(
        description="Helm dependency deduplication post-renderer",
        usage=(
            "This program collects all pre-rendered manifests from Helm\n"
            "and post-renders only those unique amongst them.\n"
            "The uniqueness is determined based on the default or supplied\n"
            "YAML keys. The keys must exist in all of the supplied documents.\n"
            "\n"
            "Invoke as --post-renderer during helm install/upgrade.\n"
            "\n"
            "You can optionally specify non-default keys by which the\n"
            "pre-rendered manifests from helm must be deduplicated:\n"
            "\n"
            "  ded --key metadata.namespace\n"
            "\n"
        ),
    )
    parser.add_argument(
        "-k",
        "--key",
        type=str,
        help="Yaml key by which the pre-rendered K8s docs must be compared",
        action="append",
        dest="keys",
    )
    return parser.parse_args()


def run():
    args = _parse()
    keys = args.keys
    if not keys:
        keys = ["kind", "metadata.name"],

    yaml = YAML()
    input_docs = yaml.load_all(sys.stdin)
    unique_docs = dict()

    for doc in input_docs:

        # Determine ID of earch supplied document
        # based on the keys
        ids = []
        for key in keys:
            # Split each key into the hierarchy of subkeys
            key_parts = key.split(".")

            try:
                # Start iterating with the top-most subkey
                value = doc[key_parts[0]]
                # Go deeper into the lower nested subkeys
                for key_part in key_parts[1:]:
                    # until values is obtainer
                    value = value[key_part]
                ids.append(str(value))

            except KeyError as ke:
                print(
                    f"Supplied document does not have required key {ke}",
                    file=sys.stderr,
                )
                print("Failed document is:", file=sys.stderr)
                yaml.dump(doc, sys.stderr)
                exit(1)

        # If document with such ID does not yet exist in our
        # collection, then add it
        id = "-".join(ids)
        if id not in unique_docs:
            unique_docs[id] = doc

    yaml.dump_all(unique_docs.values(), sys.stdout)
