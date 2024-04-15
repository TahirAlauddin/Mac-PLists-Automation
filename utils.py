#!python3
import os

def getVal(pl, path):
    """Get a value from a plist-dict by it's dot separated path"""
    # Try to access the full path level by level
    keys = path.split(".")
    curr = pl
    try:
        for key in keys:
            curr = curr[key]
    # Return None if the key doesn't exist on b
    except KeyError:
        return None
    if "CompatibilityVersion" in curr:
        return None
    return curr


def mkEntry(a, b, idx, path, isrev, res):
    """Make diff result list entry"""
    if not path in res:
        res[path] = []

    targ = res[path]

    # Generate new entry
    entry = (
        {"a": a, "b": b, "sequence": idx}
        if not isrev
        else {"a": b, "b": a, "sequence": idx}
    )

    # Don't append duplicates
    for i in targ:
        if i == entry:
            return

    targ.append(entry)


def dictEq(a, b):
    """Check whether or not two dicts equal (scalar values only)"""
    for key in a:
        if a.get(key) != b.get(key):
            return False
    return True


def diffPlists(a, b):
    """Diff two plists by checking them against each other"""
    res = {}
    # Diff a against b
    for idx, it in enumerate(a.items()):
        key = it[0]
        diffKey(a, b, key, idx, key, False, res)

    # Diff b against a
    for idx, it in enumerate(b.items()):
        key = it[0]
        diffKey(b, a, key, idx, key, True, res)
    return res


def diffKnownKeys(a, b):
    """Diff only known and unique-ifying keys, return a score of matched values"""
    knownKeys = [
        "BundlePath",
        "ExecutablePath",
        "Path",
        "Address",
        "Find",
        "Replace",
        "Identifier",
    ]

    score = 0
    for key in knownKeys:
        # Key must be in both a and b; otherwise continue
        # in other words, key not in either one of the list
        if key not in a or key not in b:
            continue

        # Increase score on matching keys
        if a.get(key) == b.get(key):
            score = score + 1

    return score


def findMostSimilar(a, lst):
    """Find most similar matching dict within list by known keys"""
    # Generate hit-list
    hits = [[b, diffKnownKeys(a, b)] for b in lst]
    hits = list(filter(lambda x: x[1] != 0, hits))

    # No similar items
    if len(hits) == 0:
        return None

    # Return most similar
    hits.sort(key=lambda x: x[1], reverse=True)
    return hits[0][0]


def diffList(b, lst, idx, path, isrev, res):
    """Diff a list by diffing it's items"""
    other = getVal(b, path)
    # Not a list, comparison impossible
    if not isinstance(other, list):
        mkEntry(lst, "<not a list>", idx, path, isrev, res)
        return

    for i in lst:
        if isinstance(i, list):
            # Nested Lists not implemented yet
            raise NotImplementedError()

        isdict = isinstance(i, dict)
        exists = False
        for j in other:
            if isinstance(i, list):
                # Nested Lists not implemented yet
                raise NotImplementedError()

            if isdict:
                # Can only compare dict against dict
                if not isinstance(j, dict):
                    continue

                # Compare dicts
                if not dictEq(i, j):
                    continue

                exists = True
                break

            # Compare scalars
            else:
                if i == j:
                    exists = True
                    break

        # Not existing exactly like this in the other list
        if not exists:
            if isdict:
                similar = findMostSimilar(i, other)
                mkEntry(
                    i,
                    similar if similar is not None else "<no entry>",
                    idx,
                    path,
                    isrev,
                    res,
                )
            else:
                mkEntry(i, "<no list partner>", idx, path, isrev, res)


def diffScalar(b, v, idx, path, isrev, res):
    """Diff a scalar value (content and type is equal)"""
    other = getVal(b, path)
    if v != other:
        mkEntry(v, other if other is not None else "<no entry>", idx, path, isrev, res)


def diffKey(a, b, k, idx, path, isrev, res):
    """Diff a key recursively (with all subkeys)"""
    val = a[k]

    # Another key to a dict
    if isinstance(val, dict):
        for key in val:
            diffKey(val, b, key, idx, f"{path}.{key}", isrev, res)
    else:
        # Diff list items
        if isinstance(val, list):
            diffList(b, val, idx, path, isrev, res)
        # Diff scalar value
        else:
            diffScalar(b, val, idx, path, isrev, res)


def validatePath(path):
    """Validate a file path to be a valid PLIST"""
    name, extension = os.path.splitext(path)
    if not os.path.isfile(path):
        raise ValueError(f'The path "{path}" does not exist!')

    if extension != ".plist" and extension != ".ccdoc":
        raise ValueError("Please only provide .plist or .ccdoc files for comparison")


def visualPrint(v):
    """Print structures optimized for readability"""
    if isinstance(v, dict):
        print("{")
        for key in v:
            val = v[key]

            # Transform bytes to hex
            if isinstance(val, bytes):
                val = val.hex().upper()

            print(f"  {key}: {val}")
        print("}")
    else:
        print(v)


def printDiffs(diffs):
    """Visualize differences"""
    # Nothing to print here
    if len(diffs) == 0:
        return

    # Find longest key length, seperator has to have at least some dashes
    keys = [key for key in diffs]
    keys.sort(key=lambda x: len(x), reverse=True)
    seplen = len(keys[0]) + 4
    seplen = seplen if seplen % 2 == 0 else seplen + 1  # make even

    # Iterate individual paths, sort by their sequence appearing in the file
    for key in sorted(
        diffs, key=lambda x: max(cdiff["sequence"] for cdiff in diffs[x])
    ):
        # Print uniform amount of dashes
        dashes = int((seplen - len(key)) / 2)
        print(f'\n{"-" * dashes}[{key}]{"-" * dashes}')

        # Print differing items for this key
        cdiffs = diffs[key]
        for i in range(0, len(cdiffs)):
            pair = cdiffs[i]
            print("A: ", end="")
            visualPrint(pair["a"])
            print("B: ", end="")
            visualPrint(pair["b"])

            # Separate using newlines
            if i != len(cdiffs) - 1:
                print()


def isScalar(v):
    """Check whether or not a value is scalar"""
    return not (isinstance(v, dict) or isinstance(v, list))


def groupParents(diffs):
    """Group scalars with the same parent into dicts"""
    newdiffs = {}
    for key in diffs:
        value = diffs[key]
        paths = key.split(".")
        parent = ".".join(paths[:-1])
        member = paths[-1]

        # Get the first value
        v = value[0]

        # Already has multiple values or is not scalar
        if len(value) > 1 or not isScalar(v["a"]) or not isScalar(v["b"]):
            newdiffs[key] = value
            continue

        # Add empty entry for this parent
        if parent not in newdiffs:
            newdiffs[parent] = [{"a": {}, "b": {}, "sequence": 0}]

        # Populate
        newdiffs[parent][0]["a"][member] = v["a"]
        newdiffs[parent][0]["b"][member] = v["b"]

        # Keep sequence number at highest value of group
        if (
            "sequence" not in newdiffs[parent][0]
            or newdiffs[parent][0]["sequence"] < v["sequence"]
        ):
            newdiffs[parent][0]["sequence"] = v["sequence"]

    return newdiffs

