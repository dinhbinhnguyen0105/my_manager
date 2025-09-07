# src/robot/action_mapping.py
from typing import Callable, Dict

from src.robot.actions.launch_browser import launch_browser
from src.robot.actions.fb_discussion import discussion
from src.robot.actions.fb_marketplace import marketplace
from src.robot.actions.fb_list_on_marketplace import list_on_marketplace
from src.robot.actions.fb_share_latest_product import share_latest_product
from src.robot.actions.fb_join_groups import join_groups
from src.robot.actions.fb_list_on_marketplace_group import list_on_marketplace_group

ACTION_MAP: Dict[str, Callable] = {
    "marketplace": marketplace,
    "list_on_group_and_share": list_on_marketplace_group,
    "launch_browser": launch_browser,
    "discussion": discussion,
    "list_on_marketplace": list_on_marketplace,
    "share_latest_product": share_latest_product,
    "join_groups": join_groups,
}
