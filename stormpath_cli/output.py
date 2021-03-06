import collections
from copy import deepcopy
from itertools import repeat
import json
import six
from sys import stdout
import logging


def _remove_links(data):
    """Removes nested/linked resources from the data output."""
    if not isinstance(data, list):
        data = [data]
    d2 = deepcopy(data)
    for i, el in enumerate(data):
        for k, v in el.items():
            if isinstance(v, dict):
                del d2[i][k]
    return d2


def _show_links(data):
    """Extracts hrefs from nested/linked resources from the data output."""
    if not isinstance(data, list):
        data = [data]
    d2 = deepcopy(data)
    for i, el in enumerate(data):
        for k, v in el.items():
            if isinstance(v, dict):
                d2[i][k] = d2[i][k].get('href')
    return d2


def _format_row(data, key, max_indent):
    """Helper function used for printing a human readable and
    nicely aligned output"""
    d = data[key] if data[key] else 'null'
    spacing = max_indent - len(key)
    spaces = "".join(repeat(" ", spacing))
    row_repr = "%s: %s%s\n" % (key, spaces, d)
    return row_repr


def _sort(data):
    """Sort the keys in the data dict alphabetically but put name and href first"""
    try:
        name = data.pop('name')
        href = data.pop('href')
    except KeyError:
        d1 = collections.OrderedDict(sorted(data.items()))
        return d1

    d1 = collections.OrderedDict(sorted(data.items()))
    d2 = collections.OrderedDict([('name', name), ('href', href)])
    d2.update(d1)
    return d2


def _output_to_tty_human_readable(data, out=stdout):
    """The default output function, used for printing a nicely aligned
    human readable output"""
    for item in data:
        ordered_data = _sort(item)
        max_indent = max(map(len, ordered_data.keys()))
        for key in ordered_data.keys():
            msg = _format_row(ordered_data, key, max_indent)
            out.write(msg)
        out.write("\n")


def _output_to_tty_json(data, out=stdout):
    """Helper function for printing JSON output"""
    out.write(json.dumps(data, indent=2, sort_keys=True))
    out.write('\n')


def _output_tsv(data, out=stdout):
    """Helper function for printing tab separates values to the output.
    Used by default when CLI output is piped"""
    if not isinstance(data, list):
        data = [data]

    if not len(data):
        return

    keys = sorted(data[0].keys())

    def force_text(val):
        # if we're including links in TSV mode, we're only interested in href
        if isinstance(val, dict) and 'href' in val:
            return val['href']
        elif val is None:
            return ''
        else:
            return str(val)

    for row in data:
        output_row = [force_text(row[key]) for key in keys]
        if six.PY3:
            d = '\t'.join(output_row)
        else:
            d = '\t'.join(output_row).encode('utf-8')
        out.write(d)
        out.write('\n')


def output(data, show_links=False, output_json=False):
    """Main output function used for printing to stdout. It will invoke the correct
    helper output function (ie. human readable/json/tsv)"""
    if not isinstance(data, list):
        data = [data]
    if not show_links:
        data = _remove_links(data)
    else:
        data = _show_links(data)

    if stdout.isatty():
        if output_json:
            _output_to_tty_json(data)
        else:
            _output_to_tty_human_readable(data)
            stdout.write("\nTotal number of Resources returned: %s\n" %
                len(data))
    else:
        _output_tsv(data)


def get_logger():
    return logging.getLogger('stormpath_cli')


def setup_output(verbose):
    """Helper function used for setting the global logging level."""
    if verbose:
        level = logging.DEBUG
    elif stdout.isatty():
        level = logging.INFO
    else:
        level = logging.ERROR

    logging.basicConfig(format='%(message)s', level=level)
    logging.getLogger("requests").propagate = False
    return get_logger()
