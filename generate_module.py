import json
import random
import re
from collections import Counter
from functools import reduce
from itertools import combinations, product, chain
from logging import fatal
from typing import List, Optional, Set, Dict, Tuple
from pydantic import BaseModel

class Result:
    _data = []

    @staticmethod
    def append_data(data: List):
        Result._data.append(data)

    @staticmethod
    def reset():
        Result._data = []

    @staticmethod
    def get():
        return Result._data

class Node(BaseModel):
    id: str
    name: str
    weight: int
    required: str

    def __init__(self, **data):
        super().__init__(**data)

def extract_variables(input_string: str) -> List[str]:
    pattern = r"[A-Z]+\d+"
    return re.findall(pattern, input_string)

def validate_dependence(node: Node, visited: Set[str], weight_summary: int) -> bool:
    dependencies = node.required
    if dependencies == "": return True
    subject_entities = extract_variables(node.required)
    for subject in subject_entities:
        dependencies = dependencies.replace(subject, " True " if subject in visited else " False ")
    dependencies = dependencies.replace("@", str(weight_summary))
    dependencies = dependencies.replace("|", " or ")
    dependencies = dependencies.replace("&", " and ")
    # print("depend: ", dependencies)
    try:
        return eval(dependencies)
    except SyntaxError as e:
        raise ValueError(f"Invalid dependency condition: {dependencies}") from e

def group_by_weight(nodes_list: List[Node]) -> Dict[int, List]:
    """Nhóm các môn theo tín chỉ"""
    storage: dict[int, list] = {}
    for node in nodes_list:
        weight: int = node.weight
        if weight not in storage:
            storage[weight] = []
        storage[weight].append(node.id)
    return storage


def group_by_count(combination_list: Set[Tuple[int]]) -> Set[Tuple[Tuple[int, int]]]:
    """Nhóm các môn theo số lượng - còn 1 môn 2 tín 3 môn 3 tín chẳng hạn"""
    result = set()

    for combination in combination_list:
        counter = Counter(combination)
        grouped_combination = tuple(sorted((value, count) for value, count in counter.items()))
        result.add(grouped_combination)

    return result


def generate_combinations(storage: List[Tuple[int, int]],
                          a: int,
                          b: int,
                          current: List[int],
                          current_sum: int,
                          result: Set[Tuple[int]]
                          ):
    """Tạo ra các tổ hợp có thể trong tổng từ a đến b"""
    if current_sum > b:
        return
    if a <= current_sum <= b:
        result.add(tuple(sorted(current)))
    for i, (value, count) in enumerate(storage):
        if count > 0:
            storage[i] = (value, count - 1)
            current.append(value)
            generate_combinations(storage, a, b, current, current_sum + value, result)
            current.pop()
            storage[i] = (value, count)

def find_combinations(nodes: Dict[str, Node], a: int, b: int) -> Set[Tuple[int]]:
    """Tìm tất cả các tổ hợp có thể xảy ra (nói chung là tiền đề cho cái hàm dưới kia kìa)"""
    storage: dict[int, list] = {}
    for node in nodes.values():
        weight: int = node.weight
        if weight not in storage:
            storage[weight] = []
        storage[weight].append(node.id)
    result = set()
    generate_combinations(list(map(lambda x: (x, len(storage[x])), storage)), a, b, [], 0, result)
    return result

def find_combinations_list(nodes_list: List[Node], a: int, b: int) -> Set[Tuple[int]]:
    """Giống cái cùng loại nhưng khác type đầu vào"""
    storage: dict[int, list] = group_by_weight(nodes_list)
    result = set()
    generate_combinations(list(map(lambda x: (x, len(storage[x])), storage)), a, b, [], 0, result)
    if not result:
        result = { tuple(node.weight for node in nodes_list) }
    return result

def travel(
        all_node: Dict[str, Node],
        opened: Set[str],
        visited: Set[str],
        range_start: int,
        range_end: int,
        current_choose: Tuple[str] = None,
        is_random: bool = True,
        phase: int = 0) -> None:
    if not opened:
        return
    if current_choose:
        print(phase, ': ', end='')
        print('opened: ', len(opened))
        print('visited: ', len(visited))
        print(current_choose)
        Result.append_data(list(current_choose))


    ways = list()

    if current_choose:
        for choice in current_choose:
            visited.add(choice)
            opened.discard(choice)
    for subject in [i for i in [j.id for j in all_node.values()] if i not in opened and i not in visited]:
        if validate_dependence(all_node[subject], visited, reduce(lambda total, subject: total + subject.weight, [all_node[i] for i in visited], 0)): opened.add(subject)


    combinations_nodes = find_combinations_list([all_node[node_id] for node_id in opened], range_start, range_end)
    iterator = group_by_count(combinations_nodes)
    opened_groups = group_by_weight([all_node[node_id] for node_id in opened])

    for i_com in iterator:
        temp = set()
        for i in i_com:
            comp = combinations(opened_groups[i[0]], i[1])
            temp.add(tuple(comp))
        for i in set(product(*temp)):
            ways.append(tuple(chain(*i)))

    if random:
        way = random.choice(ways)
        travel(all_node, opened.copy(), visited.copy(), range_start, range_end, way, is_random, phase+1)
    else:
        for way in ways:
            travel(all_node, opened.copy(), visited.copy(), range_start, range_end, way, is_random, phase+1)


def pre_travel(selected: Set[str], nodes: Dict[str, Node], range_start: int = 14, range_end: int = 20):
    print(len(nodes))
    # filtered_nodes = {key: node for key, node in nodes.items() if key not in selected}
    visited = set(selected)
    opened = set()
    for subject in nodes.values():
        total_weight = sum(node.weight for node in (nodes[i] for i in visited))
        if validate_dependence(subject, visited, total_weight):
            opened.add(subject.id)
    travel(nodes, opened, visited, range_start, range_end)

def generate_path(subjects: List, visited: List, range_start: int, range_end: int):
    nodes: Dict[str, Node] = {node_data['id']: Node(**node_data) for node_data in subjects}
    print("hasse:     " + str(nodes))
    selected = set([i.get("id") for i in visited])
    Result.reset()
    pre_travel(selected, nodes, range_start, range_end)
    return Result.get()