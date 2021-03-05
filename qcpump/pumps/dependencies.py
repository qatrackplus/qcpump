import toposort


def generate_validation_levels(dependencies):
    """Takes a dict of form:

    {
        'a': []
        'b': ['a'],
        'c': [],
        'd': ['b', 'c'],
    }
    and returns a topological sorted list of sets of dependencies like:
        [
            {'a', 'c'},  # a and c have no deps so can be calculated first at same in any order
            {'b'},       # b depends on a so has to be calculated after a
            {'d'},       # d depends on 'b', and 'c' so has to be calculated after those
        ]
    """
    deps = {s: set(ds) for s, ds in dependencies.items()}
    validation_levels = list(toposort.toposort(deps))
    return validation_levels


def generate_validation_level_subset(section, dependencies):
    """Similar to generate_validation_level but generates the levels with only the
    subset of other sections that need to be recalculated.  e.g. for

    dependencies = {
        'a': [],
        'b': ['a'],
        'c': [],
        'd': ['b', 'c'],
    }
    and section = 'b'
    generate_validation_level_subset(section, dependencies) == [{'b'}, {'d'}]
    """

    all_levels = generate_validation_levels(dependencies)

    # keep track of all sections that need to be recalculated.
    # If a section depends on any section already in this set, then
    # it needs to be recalculated too.
    to_be_recalculated = set()

    level_subsets = []

    top_level_found = False
    for level in all_levels:
        if section in level:
            # found the level with our section in it.
            top_level_found = True
            level_subsets = [{section}]
            to_be_recalculated.add(section)
        elif top_level_found:

            # find the subset of this level which needs to be recalculated
            recalc_for_this_level = set()
            for level_section in level:
                for dep in dependencies[level_section]:
                    dependency_being_recalculated = dep in to_be_recalculated
                    if dependency_being_recalculated:
                        recalc_for_this_level.add(level_section)
                        to_be_recalculated.add(level_section)

            # no need to include an empty subset
            if recalc_for_this_level:
                level_subsets.append(recalc_for_this_level)

    return level_subsets
