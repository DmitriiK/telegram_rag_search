"""things without category yet    """

from typing import List
import textwrap
from graphviz import Digraph

from src.data_classes import TelegaMessage


def visualize_topic_tree(messages: List[TelegaMessage]):
    """
    To visualize chain of messages as topic tree.
    Note: for macOS need to do: 
    brew install graphviz
    After installation, verify that the `dot` command is available in your PATH. You can check this by running the following command in your terminal:

    ```bash
    dot -V
    ```
    Args:
        messages (List[TelegaMessage]): List of Telegram Messages, from one discussion tree,
    You can use it like this:
        ```python 
        # Visualize the messages
        dot = visualize_topic_tree(topic_msgs)
        dot.attr(size='20, 40')  # Width and height (in inches)
        dot.attr(rankdir='TB')  # Top to bottom layout
        dot.render('messages_tree', format='png', cleanup=True)  # save as PNG
        display(dot)  # to display in Jupyter notebook
        ```
    Returns:
        _type_: _description_
    """
    # Create a directed graph
    dot = Digraph() 
    # Add nodes
    for message in messages:
        dot.node(str(message.msg_id), f"{message.user_name}\n{message.msg_date}\n{textwrap.fill(message.msg_text, width=30) or ''}")
        if message.reply_to_msg_id is not None:
            # Add an edge for the parent-child relationship
            dot.edge(str(message.reply_to_msg_id), str(message.msg_id))

    return dot
