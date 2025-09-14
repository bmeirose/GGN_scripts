from graphnet.models.detector.detector import Detector

class HIBEAM_Detector(Detector):
    xyz = ["x", "y", "z"]
    string_id_column = "string"
    string_index_name = "string"          # dummy names; columns need not exist
    sensor_id_column = "sensor_id"

    def feature_map(self):
        return {f: self._identity for f in ["dom_x", "dom_y", "dom_z", "dom_t"]}