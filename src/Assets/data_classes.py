import tkinter as tk
import numpy as np
import yaml
from dataclasses import dataclass, field, asdict
from typing import TypeAlias, Any, List, Dict, Tuple, Callable


# Custom representer for tuples
def represent_tuple(dumper, data):
    return dumper.represent_sequence("tag:yaml.org,2002:python/tuple", data)

# Custom constructor for tuples
def construct_tuple(loader, node):
    return tuple(loader.construct_sequence(node))

# Register the custom representer and constructor with PyYAML
yaml.add_representer(tuple, represent_tuple)
yaml.add_constructor("tag:yaml.org,2002:python/tuple", construct_tuple)


FungusType: TypeAlias = int
NyliumType: TypeAlias = int
ClearedStatus: TypeAlias = bool


@dataclass
class Dimensions:
    length: int
    width: int
    
@dataclass
class Dispenser:
    row: int
    col: int
    timestamp: int
    cleared: ClearedStatus
    
    def copy(self):
        return Dispenser(self.row, self.col, self.timestamp, self.cleared)
 
@dataclass
class PlayerlessCore:
    num_disps: int
    disp_coords: List[Dispenser]
    size: Dimensions
    nylium_type: NyliumType
    cycles: int
    blocked_blocks: List[Tuple[int, int]]
    wb_per_fungus: float
    blast_chamber_effic: float
    run_time: int
    additional_property: bool # For future use
        
    def to_yaml(self, file_path: str):
        with open(file_path, 'w') as file:
            yaml.dump(asdict(self), file)

    @classmethod
    def from_yaml(cls, file_path: str):
        with open(file_path, 'r') as file:
            data = yaml.load(file, Loader=yaml.FullLoader)
            # Convert the dictionary to the original dataclass format
            return cls.from_dict(data)
    @classmethod
    def from_dict(cls, data):
        # Convert nested dictionaries if needed
        data['disp_coords'] = [Dispenser(**disp) for disp in data['disp_coords']]
        data['size'] = Dimensions(**data['size'])
        return cls(**data)
    
    def print_types(self):
        print(f"num_disps: {type(self.num_disps)}")
        print(f"disp_coords: {type(self.disp_coords)}")
        print(f"size: {type(self.size)}")
        print(f"nylium_type: {type(self.nylium_type)}")
        print(f"cycles: {type(self.cycles)}")
        print(f"blocked_blocks: {type(self.blocked_blocks)}")
        print(f"wb_per_fungus: {type(self.wb_per_fungus)}")
        print(f"blast_chamber_effic: {type(self.blast_chamber_effic)}")
        print(f"run_time: {type(self.run_time)}")
        print(f"additional_property: {type(self.additional_property)}")
    
    def print_values(self):
        print(f"num_disps: {self.num_disps}")
        print(f"disp_coords: {self.disp_coords}")
        print(f"size: {self.size}")
        print(f"nylium_type: {self.nylium_type}")
        print(f"cycles: {self.cycles}")
        print(f"blocked_blocks: {self.blocked_blocks}")
        print(f"wb_per_fungus: {self.wb_per_fungus}")
        print(f"blast_chamber_effic: {self.blast_chamber_effic}")
        print(f"run_time: {self.run_time}")
        print(f"additional_property: {self.additional_property}")

@dataclass
class PlayerlessCoreOutput:
    total_foliage: float
    total_des_fungi: float
    bm_for_prod: float
    bm_for_grow: float
    bm_total: float
    disp_foliage_grids: np.ndarray
    disp_des_fungi_grids: np.ndarray

@dataclass
class PlayerlessCoreDistOutput:
    total_foliage_grid: np.ndarray
    total_des_fungi_grid: np.ndarray
    disp_foliage_grids: np.ndarray
    disp_des_fungi_grids: np.ndarray
    sprouts_grid: np.ndarray
    twisting_grid: np.ndarray
    bm_for_prod: float

@dataclass
class PlayerfulCore:
    num_disps: int
    clock_speed: int
    nylium_type: NyliumType

@dataclass
class PlayerfulCoreOutput:
    avg_stems: float
    avg_shrooms: float
    avg_warts: float
    stems_effic: float
    shrooms_effic: float
    wb_per_fungus: float
    vrm0s: int
    vrm1s: int
    vrm2s: int
    vrm3s: int 

@dataclass    
class DisplayInfo:
    output_label: Dict
    output_value: Dict
    info_label: Dict
    info_value: Dict
    selected_block: Tuple[int, int]

@dataclass
class SimAnnealingParams:
    optimise_func: Callable
    optimal_value: float
    initial_solution: Any
    current_solution: Any
    best_solution: Any
    start_temp: float
    end_temp: float
    cooling_rate: float
    max_iterations: int
