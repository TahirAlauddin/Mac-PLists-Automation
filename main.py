import plistlib
import argparse
import copy
from typing import List, Dict
from constants import *
from terminalTest import *
from utils import *


def delete_unnecessary_attributes(a, b):
    """Deletes unnecessary attributes from the entites that we don't care about
    For example, metadataVersion and modified"""
    for list_of_attributes in a["entities"].values():
        for attribute in list_of_attributes:
            del attribute["metadataVersion"]
            del attribute["modified"]

    for list_of_attributes in b["entities"].values():
        for attribute in list_of_attributes:
            del attribute["metadataVersion"]
            del attribute["modified"]


def get_destroyed_created_and_changed_entities(diffs: dict):
    """It will compare all the items in `diffs` and return 3 lists [destroyed, created, changed]"""
    destroyed_entity = []
    created_entity = []
    changed_entity = []

    for entity_name, entity_list in diffs.items():
        # entity_name are entities.CCAsset or entities.CCContentLink etc.
        entity_list_copy = copy.deepcopy(entity_list)
        count_a = count_b = 0

        for i in range(len(entity_list)):
            a_b_dic = entity_list[i]
            try:
                uuid_a = a_b_dic["a"]["uuid"]
            except TypeError:
                # There wass an error, it means 'a' was <no-entry>
                # Break out of loop, because rest of list's `a` is <no-entry>
                break

            for j in range(len(entity_list)):
                try:
                    a_b_dic2 = entity_list[i + j + 1]
                except IndexError:
                    # List ended, no more items to look for
                    # The entity must have been removed
                    destroyed_entity.append(a_b_dic["a"])
                    entity_list_copy[i] = None
                    # An 'A' item was read
                    count_a += 1
                    break
                try:
                    uuid_b = a_b_dic2["b"]["uuid"]
                except TypeError:
                    # 'b' was no entry, skip
                    continue
                if uuid_a == uuid_b:
                    # Duplicate values
                    changed_entity.append([a_b_dic["a"], a_b_dic2["b"]])
                    entity_list_copy[i] = None
                    entity_list_copy[i + j + 1] = None

                    # An 'A' and a 'B' item was read
                    count_a += 1
                    count_b += 1
                    break

        actual_count_b = count_items_in_entity(entity_list)[1]
        count_diff = actual_count_b > count_b
        if count_diff != 0:
            # There were some entities added in new version of plist
            # Append all entities which were added in new version
            for entity in entity_list_copy:
                if entity:
                    created_entity.append(entity["b"])

    return destroyed_entity, created_entity, changed_entity


def get_added_removed(list_a, list_b):
    """
    Takes two lists, `list_a` and `list_b`, and returns a tuple of two lists.
    The first list contains the items that were added to `list_b`, and the second list contains the items that were removed from `list_a`.

    Parameters:
    list_a (List[Any]): The old list.
    list_b (List[Any]): The new list.

    Returns:
    Tuple[List[Any], List[Any]]: A tuple of two lists, the first containing the items that were added to `list_b` and the second containing the items that were removed from `list_a`.
    """
    added = list(set(list_b) - set(list_a))
    removed = list(set(list_a) - set(list_b))
    return (added, removed)


def find_changes_in_attributes(dic1: dict, dic2: dict, entity: dict) -> list:
    """
    Compares the values of two dictionaries and returns a string containing any modifications made to the attributes of the second dictionary.
    If the value of a key in the second dictionary is different from the value of the same key in the first dictionary, the function will return a list about the modification.

    Parameters:
    dic1 (dict): The old dictionary to compare.
    dic2 (dict): The new dictionary to compare.
    entity (dict): The entity that the attributes belongs to.

    Returns:
    list: A list containing information about modifications made to the attributes of the second dictionary.
    """
    result = []
    key = dic1["name"]
    display_name = get_display_name(entity)
    item_a, item_b = dic1.get("value"), dic2.get("value")

    # If there is no value key, None != None will be False
    if item_a != item_b:
        if isinstance(item_a, list):
            added, removed = get_added_removed(item_a, item_b)
            uuids = None
            if key in ENTITIES_ITEMS_NAMES:
                # added and removed are uuids of entities_items
                # Collections have changed
                added, removed, uuids = get_display_names_from_entity_item_uuids(
                    added, removed
                )
            elif key in ENTITIES_COLLECTIONS_NAMES:
                # added and removed are uuids of entities_collections
                # Groups have changed
                added, removed, uuids = get_display_names_from_entity_collection_uuids(
                    added, removed
                )
            if uuids:
                result.extend([uuids, entity["name"], display_name, key])
            else:
                result.extend([entity['uuid'], entity["name"], display_name, key])
            if added:
                result.extend([",".join(added), "added"])
            if removed:
                result.extend([",".join(removed), "removed"])
        else:
            if display_name:
                result.extend(
                    [entity["uuid"], entity["name"], display_name, key, item_a, item_b, "changed"]
                )
            else:
                # If the entity was an asset, it is a boolean value
                if entity["name"] == 'CCAsset':
                    # old_value = item_a
                    # new_value = item_b
                    result.extend(
                        [entity["uuid"], entity["name"], key, item_a, item_b, "changed"]
                    )
                elif entity['name'] == 'CCNotification':
                    result.extend(
                        [entity["uuid"], entity["name"], key, item_a, item_b, "changed"]
                    )
                
                else:
                    pass
                    # print(f"Skipping an entity. This entity {entity['name']} will not be tracked for modification")

    return result


def get_display_names_from_entity_collection_uuids(
    added: List[str], removed: List[str]
):

    display_names_removed = []
    display_names_added = []
    uuids = []

    for uuid in added:
        uuids.append(uuid)
        entity_collection = entities_collections_b[uuid]
        display_name = get_display_name(entity_collection)
        display_names_added.append(display_name)

    for uuid in removed:
        uuids.append(uuid)
        entity_collection = entities_collections_a[uuid]
        display_name = get_display_name(entity_collection)
        display_names_removed.append(display_name)

    return display_names_added, display_names_removed, uuids


def get_display_names_from_entity_item_uuids(added: List[str], removed: List[str]):

    display_names_removed = []
    display_names_added = []
    uuids = []

    for uuid in added:
        uuids.append(uuid)
        entity_item = entities_items_b[uuid]
        for attr in entity_item["attributes"]:
            entity_id = attr["value"]
            entity = entities_b[entity_id]
            display_name = get_display_name(entity)
            display_names_added.append(display_name)

    for uuid in removed:
        uuids.append(uuid)
        entity_item = entities_items_a[uuid]
        for attr in entity_item["attributes"]:
            entity_id = attr["value"]
            entity = entities_a[entity_id]
            display_name = get_display_name(entity)
            display_names_removed.append(display_name)

    return display_names_added, display_names_removed, uuids


def find_changes_in_entities(entity: List[Dict]) -> tuple:
    """
    Takes in a list of two entities and returns a tuple of list containing any modifications made to the attributes of the second entity.
    It compares the attributes of the first entity with the attributes of the second entity and returns the differences.

    Parameters:
    entity (list): A list of two entities

    Returns:
    tuple: A string containing modifications made to the attributes of the second entity
    """
    a, b = entity
    non_list_modifications = []
    list_type_modifications = []
    for attr_a, attr_b in zip(a["attributes"], b["attributes"]):
        modifications = find_changes_in_attributes(attr_a, attr_b, a)
        if modifications:
            if modifications[-1] == 'changed':
                non_list_modifications.append(modifications)
            else:
                if len(modifications) == 8:
                    # There was something removed as well as added 
                    # TODO: don't add the whole uuid
                    #! Might be problems later
                    len_of_added = len(modifications[4].split(','))
                    if isinstance(modifications[0], list):
                        list_type_modifications.append([modifications[0][:len_of_added]] + modifications[1:4] + modifications[4:6])
                        list_type_modifications.append([modifications[0][len_of_added:]] + modifications[1:4] + modifications[6:8])
                    else:
                        # When the key is ContentFilters, or others if added later
                        list_type_modifications.append(modifications[:4] + modifications[4:6])
                        list_type_modifications.append(modifications[:4] + modifications[6:8])
                else:
                    # There was something either removed or added, not both
                    list_type_modifications.append(modifications)

    for bundle_a, bundle_b in zip(a["bundleStyle"].items(), b["bundleStyle"].items()):
        modifications = find_changes_in_bundle_style(bundle_a, bundle_b, a)
        if modifications:
            non_list_modifications.append(modifications)

    return (list_type_modifications, non_list_modifications)

def find_changes_in_bundle_style(bundle_a: tuple, bundle_b: tuple, entity):
    uuid = entity['uuid']
    entity_name = entity['name']
    old_key, old_value = bundle_a # bundle_a is expected to be a tuple of 2 items
    new_key, new_value = bundle_b # bundle_b is expected to be a tuple of 2 items
    if old_key == new_key and old_value != new_value:
        # Different values
        return uuid, entity_name, old_key, old_value, new_value, 'critical change'



def get_display_name(entity: dict) -> str:
    """Returns the human readable display name of an entity
    It can be get from either `DisplayName` attribute"""
    if entity["name"] == "CCAsset":
        return ""
    display_name = get_attribute_in_entity("DisplayName", entity)
    return display_name


def convert_difference_to_human_readable_text(
    destroyed_entities: List[Dict],
    created_entities: List[Dict],
    modified_entities: List[List[Dict]],
) -> tuple:
    """
    convert_difference_to_human_readable_text

    This function takes in three lists of dictionaries: destroyed_entities, created_entities, and modified_entities.
    It converts the differences between the entities in these lists into human-readable text.
    The function returns a list of strings containing the text describing the differences.
    """
    modified_entities_message = ""
    created_entities_message = ""
    destroyed_entities_message = ""
    total_events = []
    uuids = []; events = []
    display_names = []
    entity_names = []
    list_type_modifications = []
    nonlist_modifications = []

    # ENTITY Was Created
    for entity in created_entities:
        display_name = get_display_name(entity)
        if display_name:
            uuids.append(entity["uuid"])
            events.append("created")
            display_names.append(display_name)
            entity_names.append(entity["name"])
        else:
            if entity["name"] in ['CCAsset', 'CCContentFilterAvailability', 'CCContentFilterLanguage',]: # Contains Description
                display_name = get_attribute_in_entity('Description', entity)
            elif entity["name"] in ['CCNotification']: # Contains 'AccessibilityText'
                display_name = get_attribute_in_entity('AccessibilityText', entity)
            else:
                display_name = ''
            uuids.append(entity["uuid"])
            events.append("created")
            display_names.append(display_name)
            entity_names.append(entity["name"])

    # Create Table for created entities
    created_entities_message += Print_Entities_Tables(
        entity_names, display_names, events, uuids
    )

    #! Important
    # Make sure the lists are empty again
    total_events.extend(events) # For the sake of summary, we need all events
    uuids = []; events = []
    display_names = []
    entity_names = []

    # ENTITY Was Destroyed
    for entity in destroyed_entities:
        display_name = get_display_name(entity)
        if display_name:
            uuids.append(entity["uuid"])
            events.append("destroyed")
            display_names.append(display_name)
            entity_names.append(entity["name"])
        else:
            if entity["name"] in ['CCAsset', 'CCContentFilterAvailability', 'CCContentFilterLanguage', ]: # Contains Description
                display_name = get_attribute_in_entity('Description', entity)
            elif entity["name"] in ['CCNotification']:                                                    # Contains AccessibilityText
                display_name = get_attribute_in_entity('AccessibilityText', entity)
            else:
                display_name = ''
            uuids.append(entity["uuid"])
            events.append("destroyed")
            display_names.append(display_name)
            entity_names.append(entity["name"])

    # Create Table for created entities
    destroyed_entities_message += Print_Entities_Tables(
        entity_names, display_names, events, uuids
    )
    total_events.extend(events) # For the sake of summary, we need all events


    # ENTITY Was changed/modification
    for entity in modified_entities:
        list_type_modification, nonlist_modification = find_changes_in_entities(entity)
        if list_type_modification:
            for modification in list_type_modification:
                list_type_modifications.append(modification)
        if nonlist_modification:
            nonlist_modifications.extend(nonlist_modification)
                
    # Send content_filters_a and content_filters_b for the exception
    modified_entities_message += Print_Entities_Changed_For_Lists_Tables(list_type_modifications, content_filters_a_data,
                                                content_filters_b_data, content_filters_region_a_data, content_filters_region_b_data)
    modified_entities_message += '\n'

    modified_entities_message += Print_Entities_Changed_Tables(nonlist_modifications)
    modified_entities_message += '\n'
    
    global summary
    summary = generate_summary(total_events, list_type_modifications, nonlist_modifications, 
                                plist_entities_a['version'], plist_entities_b['version'])

    return destroyed_entities_message, created_entities_message, modified_entities_message


def print_entities(
    destroyed_entities_message, created_entities_message, modified_entities_message,
    selection=None
    ):
    """Prints the human readable messages about created entities, destroyed entities
    and modified entities on the terminal"""
    if not selection:
        selection = input("Select from the following Reports: [Full Dev Report => 1 | Consumer-Facing Report => 2] ")
    if selection == '1':
        # long report
        print(created_entities_message)
        print(destroyed_entities_message)
        print(modified_entities_message)
        print(summary)

    elif selection == '2':
        # short report
        print(destroyed_entities_message)
        print(modified_entities_message)
        print(summary)
        
    else:
        print("Invalid selection")
        print_entities(
            destroyed_entities_message, created_entities_message, modified_entities_message,
            selection
        )


def count_items_in_entity(entity: list):
    """Counts the items in an entity"""
    count_a = count_b = 0

    for item in entity:
        if item["a"] != "<no entry>":
            count_a += 1
        else:
            count_b += 1
    return count_a, count_b


def get_attribute_in_entity(attribute: str, entity_item: list):
    """
    This function takes an 'attribute' name as a string and a 'entity_item' as a list.
    It will iterate through the attributes in the entity_item and if it finds a match for the attribute name,
    it will return the value of that attribute. If no match is found, the function will return None.
    """
    for attr in entity_item["attributes"]:
        if attr["name"] == attribute:
            return attr.get("value", '')


def get_entities_data(plist_entities):
    result = {}
    for name, entity in plist_entities["entities"].items():
        if name in ENTITIES_NAMES_KEYS:
            for attr in entity:
                result[attr["uuid"]] = attr

    return result


def get_entities_items_data(plist_entities):
    result = {}
    for name, entity in plist_entities["entities"].items():
        if name in ENTITIES_ITEMS_NAMES_KEYS:
            for attr in entity:
                result[attr["uuid"]] = attr

    return result


def get_entities_collections_data(plist_entities):
    result = {}
    for name, entity in plist_entities["entities"].items():
        if name in ENTITIES_COLLECTIONS_NAMES_KEYS:
            for attr in entity:
                result[attr["uuid"]] = attr

    return result


def get_assets_data(plist_entities: dict) -> dict:
    """
    Get assets from a plist.

    This function takes plist entities (in the form of a dictionary) as input and returns a new dictionary containing all assets from the input,
    with the asset's UUID as the key and the asset itself as the value.

    Args:
    plist_entities (dict): The input plist entities.

    Returns:
    dict: A dictionary containing all assets from the input.
    """
    return {asset["uuid"]: asset for asset in plist_entities["entities"]["CCAsset"]}


def get_content_filters_language_data(plist_entities: dict) -> dict:
    """Get CCContentFiltersLanguage from a plist."""
    return {content_filter["uuid"]: content_filter for content_filter in plist_entities["entities"]["CCContentFilterLanguage"]}
    

def get_content_filters_region_data(plist_entities: dict) -> dict:
    """Get CCContentFiltersRegion from a plist."""
    return {content_filter["uuid"]: content_filter for content_filter in plist_entities["entities"]["CCContentFilterAvailability"]}
    

def compare_ccdoc(file_path_a, file_path_b, selection=None):
    
    global plist_entities_a, plist_entities_b
    global entities_a, entities_b, entities_items_a, entities_items_b, assets_a, assets_b
    global entities_collections_a, entities_collections_b
    global content_filters_a_data, content_filters_b_data
    global content_filters_region_a_data, content_filters_region_b_data

    # Open both files and invoke diffing
    with open(file_path_a, "rb") as file_a:
        with open(file_path_b, "rb") as file_b:
            plist_entities_a, plist_entities_b = plistlib.load(file_a), plistlib.load(
                file_b
            )

            # Delete modified and metadataVersion
            delete_unnecessary_attributes(plist_entities_a, plist_entities_b)

            entities_items_a = get_entities_items_data(plist_entities_a)
            entities_items_b = get_entities_items_data(plist_entities_b)

            entities_a = get_entities_data(plist_entities_a)
            entities_b = get_entities_data(plist_entities_b)

            assets_a = get_assets_data(plist_entities_a)
            assets_b = get_assets_data(plist_entities_b)

            entities_collections_a = get_entities_collections_data(plist_entities_a)
            entities_collections_b = get_entities_collections_data(plist_entities_b)

            content_filters_a_data = get_content_filters_language_data(plist_entities_a)
            content_filters_b_data = get_content_filters_language_data(plist_entities_b)

            content_filters_region_a_data = get_content_filters_region_data(plist_entities_a)
            content_filters_region_b_data = get_content_filters_region_data(plist_entities_b)


            diffs = diffPlists(plist_entities_a, plist_entities_b)
            destroyed_entity, created_entity, changed_entity = get_destroyed_created_and_changed_entities(diffs)
            (
                destroyed_entities_text,
                created_entities_text,
                modified_entities_text,
            ) = convert_difference_to_human_readable_text(
                destroyed_entity, created_entity, changed_entity
            )
            print_entities(
                destroyed_entities_text, created_entities_text, modified_entities_text,
                selection
            )



def main():
    """Main entry-point of the program"""
    # Parse required and optional arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", dest="a", help="Absolute path to file A", required=True)
    parser.add_argument("-b", dest="b", help="Absolute path to file B", required=True)
    args = parser.parse_args()

    validatePath(args.a)
    validatePath(args.b)

    compare_ccdoc(args.a, args.b)


if __name__ == "__main__":
    main()
