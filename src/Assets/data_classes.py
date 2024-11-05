import tkinter as tk
import numpy as np
from dataclasses import dataclass, field
from typing import TypeAlias, Any, List, Dict, Tuple, Callable

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
    nylium_type: NyliumType | tk.StringVar 
    cycles: int
    blocked_blocks: List[List[int]]
    warts_effic: float | tk.StringVar 
    blast_chamber_effic: float | tk.StringVar
    run_time: int
    randomised: bool

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
    sprouts_total: np.ndarray
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
    warts_effic: float
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
