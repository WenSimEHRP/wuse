from string import Template
import re

class LabelEnums:
    def __init__(self, labels):
        self.labels = labels
        self.enums = {label: ind for ind, label in enumerate(labels)}
        self.switch_string_dict = self.construct_string("${ind}: ${ind}_value;")
        self.enum_string_dict = self.construct_string("const ${ind}_value = ${val};")
        self.enum_string_dict_no_value = self.construct_string("const ${ind} = ${val};")
        self.define_string_dict = self.construct_string("#define ${ind} ${val}")

    def construct_string(self, template):
        a = {}
        for ind, val in self.enums.items():
            if not isinstance(ind, (list, tuple, set, dict)):
                a[ind] = Template(template).substitute(ind=ind, val=val)
            else:
                for i in ind:
                    a[i] = Template(template).substitute(ind=i, val=val)
        return a

    @property
    def switch_string(self):
        a = []
        for ind, val in self.switch_string_dict.items():
            if val is None:
                continue
            if ind.endswith("_cond_0"):
                basename = ind.replace("_cond_0", "")
                a.append(f"{basename}: sw_{basename}_conditional();")
            elif re.match(r".*cond_\d+$", ind):
                continue
            else:
                a.append(val)
        return "\n".join(a)

    @property
    def enum_string(self):
        a = [i for i in self.enum_string_dict.values() if i is not None]
        return "\n".join(a)

    @property
    def enum_string_no_value(self):
        a = [i for i in self.enum_string_dict_no_value.values() if i is not None]
        return "\n".join(a)

    @property
    def define_string(self):
        a = [i for i in self.define_string_dict.values() if i is not None]
        return "\n".join(a)

road_labels = (
    "ORD0",  # FIELD ROAD
    "ROAD_cond_0",  # DIRT ROAD
    "ROAD_cond_1",
    "ORD2",  # SAND ROAD
    "ORD3",  # GRAVEL ROAD
    "SRD0",  # PAVED STONE ROAD
    "SRD1",  # CONCRETE ROAD
    "SRD2",  # CONCRETE SLAB OF ROAD
    "SRD3",  # CONCRETE SLAB OF ROAD
    "TRD0_cond_0",  # TOWN ROAD, has special conditions
    "TRD0_cond_1",
    "ARD0",  # ASPHALT ROAD
    "ARD1",  # ASPHALT ROAD W/LINES
    "ARD2",  # ROAD CLASS B
    "ARD3",  # ROAD CLASS B
    "ARD4",  # ROAD CLASS A
    "WRD0",  # HIGHWAY
    "WRD1",  # EXPRESSWAY
    "URD0",  # RESIDENTIAL ROAD
    "URD1",  # URBAN ROAD
    "URD2",  # GREEN ROAD
    "URD3",  # RED ROAD
    "URD4",  # GRAY PAVEMENT
    "URD5",  # WHITE PAVEMENT
    "URD6",  # PEDESTRIAN ZONE
    "DRD0",  # MUD DIRT ROAD
    "DRD1",  # COBBLESTONES ROAD
    "DRD2",  # ISR ROAD
    "DRD3",  # CEMENT SLAB ROAD
    "DRD4",  # CONCRETE ROAD (BLACK)
    "DRD5",  # CONCRETE ROAD (GRAY)
    "DRD6",  # CONCRETE ROAD (WHITE)
    "ELRD",  # STONE PAVED ROAD (ELECTRIFIED)
    "AER0",  # ASPHALT ROAD
    "AER2",  # ROAD CLASS C
    "AER3",  # ROAD CLASS B
    "UER0",  # RESIDENTIAL ROAD
    "UER1",  # URBAN ROAD
    "UER5",  # WHITE PAVEMENT (ELECTRIFIED)
)
road_enum = LabelEnums(road_labels)

temp_registers = ("SW_ROADTYPE", "SW_TRAMTYPE", "SW_VIEW", "SW_SETUP_N_PLAT", "SW_SETUP_S_PLAT", "SW_GROUND")
temp_enum = LabelEnums(temp_registers)

tram_labels = (
    "RAIL", # TRAM TRACK
    "ELRL", # TRAM TRACK (ELECTRIFIED)
    "TRL0", # MODERN TRAM TRACK
    "TEL0", # MODERN TRAM TRACK (ELECTRIFIED)
    "UEL0", # URBAN TRAM TRACK (ELECTRIFIED)
    "UEL1", # RED TRAM TRACK (ELECTRIFIED)
    "UEL2", # GREEN TRAM TRACK (ELECTRIFIED)
    "DRL0", # ISR TRAM TRACK
    "DEL0", # ISR TRAM TRACK (ELECTRIFIED)
)
tram_enum = LabelEnums(tram_labels)

position_labels = ("POS_N","POS_NE","POS_E","POS_SE","POS_S","POS_SW","POS_W","POS_NW","POS_C")
position_enum = LabelEnums(position_labels)

bit_enum = LabelEnums(("BIT_N_PLAT", "BIT_S_PLAT"))

with open("src/switches.pynml", "r") as f:
    data_template = f.read()

data = Template(data_template).substitute(
    roadtype_enums=road_enum.enum_string,
    tramtype_enums=tram_enum.enum_string,
    tempstore_enums=temp_enum.enum_string_no_value,
    roadtype_switch_cases=road_enum.switch_string,
    tramtype_switch_cases=tram_enum.switch_string,
    position_enums=position_enum.enum_string_no_value,
    bit_enums=bit_enum.enum_string_no_value,
)

with open("src/switches.pnml", "w+") as f:
    f.write(data)
