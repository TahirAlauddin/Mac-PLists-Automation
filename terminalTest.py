#!/usr/bin/env python
from __future__ import print_function

from colorclass import Color
from terminaltables import SingleTable
from constants import *
from textwrap import wrap


def group_data(data, index=0):
    grouped_data = {}
    for row in data:
        key = row[index]
        if key in grouped_data:
            grouped_data[key].append(row[:index] + row[index+1:])
        else:
            grouped_data[key] = [row[:index] + row[index+1:]]
    return grouped_data


def generate_summary(events, list_type_modification, nonlist_modification, catalog_a, catalog_b):
    added_count = removed_count = modified_count = created_count = destroyed_count = 0
    
    # count created and destroyed entities
    for event in events:
        if event == 'created':
            created_count += 1
        else:
            destroyed_count += 1

    # count added, removed and modified entities
    for uuids, *_, event in list_type_modification:
        if isinstance(uuids, list):
            if event == 'added':
                added_count += len(uuids)
            else:
                removed_count += len(uuids)
        else:
            if event == 'added':
                added_count += 1
            else:
                removed_count += 1

    for _ in nonlist_modification:
        modified_count += 1

    # Generate the summary message
    summary = ""
    summary += f'Summary:\n'
    summary += f'Summary for {catalog_a} -> {catalog_b}\n'
    summary += f'{created_count} were created\n'
    summary += f'{destroyed_count} were destroyed\n'
    summary += f'{added_count} were added\n'
    summary += f'{removed_count} were removed\n'
    summary += f'{modified_count} were modified\n'

    return summary


def Print_Entities_Tables(entity_names, display_names, events, uuids):
    """Return table string to be printed."""
    tables = ''
    group_by_entities_name: dict = group_data(zip(entity_names, display_names, events, uuids))
    for entity_name, list_of_rows in group_by_entities_name.items():
        table_data = [
            [Color('UUID'), Color('Asset'), Color('Event')],
        ]
        for (display_name, event, uuid) in list_of_rows: 
            if event == 'created':
                color = 'autogreen'
            else:
                color = 'autored'
            if display_name != '':
                table_data.append( [Color(uuid), Color(display_name), Color(f'{{{color}}}%s{{/{color}}}' % event)] )
        
        if len(table_data) <= 1:
            continue
        table_instance = SingleTable(table_data, entity_name)
        # table_instance.inner_heading_row_border = False
        table_instance.inner_row_border = True
        table_instance.justify_columns = {0: 'center', 1: 'center', 2: 'center'}
        tables += table_instance.table + '\n\n\n'

    return tables


def Print_Assets_Changed_Table(assets_changed):
    table_data = [
            [Color('UUID'), Color('Key'), Color('Old Value'), Color('New Value'), Color('Event')],
        ]
    for (uuid, key, old_value, new_value, event) in assets_changed:
        table_data.append( [Color(uuid), Color(key), Color('\n'.join(wrap(str(old_value), 40))),
                            Color('\n'.join(wrap(str(new_value), 40))), 
                            Color('{autoblue}%s{/autoblue}' % event)] )
    
    # Prevent creating an empty table
    if len(table_data) <= 1:
        return ''

    table_instance = SingleTable(table_data, f"Value Changed Assets")
    # table_instance.inner_heading_row_border = False
    table_instance.inner_row_border = True
    table_instance.justify_columns = {0: 'center', 1: 'center', 2: 'center'}

    return table_instance.table + '\n\n\n'


def Print_Entities_Changed_Tables(modifications):
    """Return table string to be printed."""
    # This function here is used for the entities that were changed
    tables = ''
    group_by_entities_name = group_data(modifications, index=1)
    assets_changed = []
    bundle_changed = []
    other_entities_changed = {}
    for entity_name, list_of_rows in group_by_entities_name.items():
        table_data = [
            [Color('UUID'), Color('Display Name'), Color('Key'), Color('Old Value'), Color('New Value'), Color('Event')],
        ]
        #! Comment CCAsset logic
        if entity_name == 'CCAsset':
            assets_changed.extend(list_of_rows)
            continue
        elif entity_name == 'CCNotification':
            other_entities_changed[entity_name] = list_of_rows
            continue
        
        for row in list_of_rows:
            if len(row) == 6:
                (uuid, display_name, key, old_value, new_value, event) = row
                table_data.append( [Color(uuid), Color(display_name), Color(key), 
                                    Color('\n'.join(wrap(old_value, 40))), 
                                    Color('\n'.join(wrap(new_value, 40))),
                                    Color('{autoblue}%s{/autoblue}' % event)] )
            elif len(row) == 5:
                bundle_changed.append([entity_name] + list(row))
                # BundleStyle was changed
        if len(table_data) > 1:
            table_instance = SingleTable(table_data, f"Value Changed {entity_name}")
            # table_instance.inner_heading_row_border = False
            table_instance.inner_row_border = True
            table_instance.justify_columns = {0: 'center', 1: 'center', 2: 'center'}
            tables += table_instance.table + '\n\n\n'

        
    table_data = [
                    [Color('UUID'), Color('Entity Name'), Color('Key'), Color('Old Value'), Color('New Value'), Color('Event')],
                 ]
    for row in bundle_changed:
        (entity_name, uuid, key, old_value, new_value, event) = row
        table_data.append( [Color(uuid), Color(entity_name), Color(key), 
                            Color('\n'.join(wrap(str(old_value), 40))), 
                            Color('\n'.join(wrap(str(new_value), 40))),
                            Color.colorize('magenta', event)] )

    if len(table_data) > 1:
        table_instance = SingleTable(table_data, f"BundleStyle Changed")
        table_instance.inner_row_border = True
        table_instance.justify_columns = {0: 'center', 1: 'center', 2: 'center'}
        tables += table_instance.table + '\n\n\n'


    # Entities which do not have display name
    # Less important entities like CCNotification etc.
    for entity_name, rows in other_entities_changed.items():
        table_data = [
                        [Color('UUID'), Color('Key'), Color('Old Value'), Color('New Value'), Color('Event')],
                     ]
        for row in rows:
            (uuid, key, old_value, new_value, event) = row
            table_data.append( [Color(uuid), Color(key), 
                                Color('\n'.join(wrap(str(old_value), 40))), 
                                Color('\n'.join(wrap(str(new_value), 40))),
                                Color.colorize('blue', event)] )

        if len(table_data) > 1:
            table_instance = SingleTable(table_data, f"{entity_name} Changed")
            table_instance.inner_row_border = True
            table_instance.justify_columns = {0: 'center', 1: 'center', 2: 'center'}
            tables += table_instance.table + '\n\n\n'


    # Changes made in Assets
    tables += Print_Assets_Changed_Table(assets_changed)

    return tables


def Print_Entities_Changed_For_Lists_Tables(modifications, *args):
    """Return table string to be printed."""
    # This function here is used for the entities that were added or removed
    tables = ''
    tables += '------------------------\n'
    tables += 'These values were modified:'
    tables += '\n\n\n\n'
    content_filters = []
    group_by_entities_name = group_data(modifications, index=1)
    for entity_name, list_of_rows in group_by_entities_name.items():
        table_data = [
            [Color('UUID'), Color('Display Name'), Color('Attribute'), Color('Value'), Color('Event')],
        ]
        for (uuids, display_name, key, value, event) in list_of_rows: 
            if event == 'added':
                color = 'autogreen'
            else:
                color = 'autored'
                
            if isinstance(uuids, list):
                # More than 1 value added or removed in an attribute
               for uuid, sub_value in zip(uuids, value.split(',')):
                    table_data.append( [Color(uuid), Color(display_name), Color(key), Color(sub_value),
                                        Color(f'{{{color}}}%s{{/{color}}}' % event)] )
            else:
                if key == 'ContentFilters':
                    content_filters.append([uuids, entity_name, display_name, key, value, event, color])
                    continue
                table_data.append( [Color(uuids), Color(display_name), Color(key), Color(value),
                                    Color(f'{{{color}}}%s{{/{color}}}' % event)] )
        
        # Make sure no empty table is printed
        if len(table_data) <= 1:
            continue

        table_instance = SingleTable(table_data, f"Changed {entity_name}")
        # table_instance.inner_heading_row_border = False
        table_instance.inner_row_border = True
        table_instance.justify_columns = {0: 'center', 1: 'center', 2: 'center'}
        tables += table_instance.table + '\n\n\n'


    if content_filters:
        table_data = [
            [Color('UUID'), Color('Entity Name'), Color('Description'), Color('Countries'), Color('Extension'), Color('Event')],
        ]
        if args:
            for content_filter in content_filters:
                uuid, entity_name, display_name, key, value, event, color = content_filter
                try:
                    if event == 'added':
                        content_filter_data = args[1] # content_filters_b
                    else:
                        content_filter_data = args[0] # content_filters_a
                    content_filter = content_filter_data[value]
                except:
                    if event == 'added':
                        content_filter_data = args[3] # content_filters_region_b
                    else:
                        content_filter_data = args[2] # content_filters_region_a
                    content_filter = content_filter_data[value]
                description, countries, exclusion = get_description_countries_exclusion_from_content_filters(content_filter)
                table_data.append( [Color(uuid), Color(f"{entity_name}: {display_name}"), Color('\n'.join(wrap(description, 30))), 
                                    Color('\n'.join(wrap(countries, 30))), Color(exclusion),
                                    Color(f'{{{color}}}%s{{/{color}}}' % event)] )

        table_instance = SingleTable(table_data, f"ContentFilters")
        # table_instance.inner_heading_row_border = False
        table_instance.inner_row_border = True
        table_instance.justify_columns = {0: 'center', 1: 'center', 2: 'center'}
        tables += table_instance.table + '\n\n'

    return tables  

def get_description_countries_exclusion_from_content_filters(content_filter):
    description = countries = exclusion = None
    for attribute in content_filter['attributes']:
        if attribute['name'] == 'Description':
            description = attribute['value']
        elif attribute['name'] == 'Exclusion Type':
            exclusion = attribute['value']
        elif attribute['name'] in ['FilteredLanguages', 'FilteredRegions']: 
            countries = ', '.join(attribute['value'])
    
    return description, countries, exclusion    
