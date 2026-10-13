"""Behavior checks for the self-contained CT/SEG tutorial definitions.

Run after installing the notebook's dependencies:
    python -m pytest test/src/test_ct_seg_to_tensors.py
"""
import copy
from pathlib import Path

import highdicom as hd
import nbformat
import numpy as np
import pydicom
import pytest
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.uid import CTImageStorage, ExplicitVRLittleEndian, generate_uid


NOTEBOOK = Path(__file__).resolve().parents[2] / "notebooks/advanced_topics/ct_seg_to_tensors.ipynb"
namespace = {}
for cell in nbformat.read(NOTEBOOK, as_version=4).cells:
    if "definitions" in cell.metadata.get("tags", []):
        exec(compile(cell.source, str(NOTEBOOK), "exec"), namespace)
convert = namespace["validate_and_convert"]
split_patients = namespace["patient_disjoint_split"]
ValidationError = namespace["ValidationError"]


@pytest.fixture
def pair():
    study, series, frame_of_reference = generate_uid(), generate_uid(), generate_uid()
    images = []
    for z in (0, 5, 10):
        image = Dataset()
        image.file_meta = FileMetaDataset()
        image.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
        image.SOPClassUID = CTImageStorage
        image.SOPInstanceUID = generate_uid()
        image.PatientID = "tutorial-patient"
        image.PatientName = "Synthetic^Patient"
        image.PatientBirthDate = ""
        image.PatientSex = ""
        image.StudyInstanceUID = study
        image.SeriesInstanceUID = series
        image.FrameOfReferenceUID = frame_of_reference
        image.StudyID = "1"
        image.SeriesNumber = 1
        image.InstanceNumber = z + 1
        image.StudyDate = "20260101"
        image.StudyTime = "120000"
        image.AccessionNumber = ""
        image.Modality = "CT"
        image.ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
        image.ImagePositionPatient = [0, 0, z]
        image.PixelSpacing = [2, 3]
        image.SliceThickness = 5
        image.Rows, image.Columns = 4, 4
        image.SamplesPerPixel = 1
        image.PhotometricInterpretation = "MONOCHROME2"
        image.BitsAllocated = 16
        image.BitsStored = 16
        image.HighBit = 15
        image.PixelRepresentation = 0
        image.RescaleSlope = 2
        image.RescaleIntercept = -1000
        image.RescaleType = "HU"
        image.PixelData = np.full((4, 4), z + 1, dtype=np.uint16).tobytes()
        images.append(image)
    masks = np.zeros((3, 4, 4, 2), dtype=np.uint8)
    masks[0, 1, 2, 0] = 1
    masks[2, 2, 1, 0] = 1
    masks[2, 2, 1, 1] = 1  # Intentional overlap must survive conversion.
    descriptions = [
        hd.seg.SegmentDescription(
            segment_number=number, segment_label=label,
            segmented_property_category=pydicom.sr.codedict.codes.SCT.AnatomicalStructure,
            segmented_property_type=code,
            algorithm_type=hd.seg.SegmentAlgorithmTypeValues.MANUAL,
        )
        for number, label, code in [
            (1, "Kidney", pydicom.sr.codedict.codes.SCT.Kidney),
            (2, "Liver", pydicom.sr.codedict.codes.SCT.Liver),
        ]
    ]
    seg = hd.seg.Segmentation(
        source_images=images, pixel_array=masks,
        segmentation_type=hd.seg.SegmentationTypeValues.BINARY,
        segment_descriptions=descriptions, omit_empty_frames=False,
        series_instance_uid=generate_uid(), series_number=2,
        sop_instance_uid=generate_uid(), instance_number=1,
        manufacturer="Tutorial", manufacturer_model_name="Synthetic",
        software_versions="1", device_serial_number="1",
    )
    return images, copy.deepcopy(seg)


def test_ct_order_hu_affine_and_overlapping_mask_channels(pair):
    images, seg = pair
    image, masks, metadata = convert([images[2], images[0], images[1]], seg, 3)
    assert image.shape == (1, 3, 4, 4)
    assert image.dtype == np.float32
    assert image[0, :, 0, 0].tolist() == [-998, -988, -978]
    np.testing.assert_allclose(metadata["affine_dhw_to_lps_mm"],
                               [[0, 0, 3, 0], [0, 2, 0, 0], [5, 0, 0, 0], [0, 0, 0, 1]])
    assert masks.dtype == np.uint8
    assert masks[:, 2, 2, 1].tolist() == [1, 1]
    assert sorted(np.count_nonzero(mask) for mask in masks) == [1, 2]


@pytest.mark.parametrize("change, message", [
    ("patient", "PatientID mismatch"),
    ("series", "different CT series"),
    ("frame_of_reference", "FrameOfReferenceUID mismatch"),
    ("position", "SEG position differs"),
    ("spacing", "SEG pixel spacing differs"),
    ("orientation", "SEG orientation differs"),
    ("spatial_no", "does not preserve"),
])
def test_incompatible_pair_is_rejected(pair, change, message):
    images, seg = pair
    if change == "patient":
        seg.PatientID = "wrong-patient"
    elif change == "series":
        seg.ReferencedSeriesSequence[0].SeriesInstanceUID = generate_uid()
    elif change == "frame_of_reference":
        seg.FrameOfReferenceUID = generate_uid()
    elif change == "position":
        seg.PerFrameFunctionalGroupsSequence[0].PlanePositionSequence[0].ImagePositionPatient = [1, 0, 0]
    elif change == "spacing":
        seg.SharedFunctionalGroupsSequence[0].PixelMeasuresSequence[0].PixelSpacing = [1, 1]
    elif change == "orientation":
        seg.SharedFunctionalGroupsSequence[0].PlaneOrientationSequence[0].ImageOrientationPatient = [0, 1, 0, 1, 0, 0]
    else:
        seg.PerFrameFunctionalGroupsSequence[0].DerivationImageSequence[0].SourceImageSequence[0].SpatialLocationsPreserved = "NO"
    with pytest.raises(ValidationError, match=message):
        convert(images, seg, 3)


@pytest.mark.parametrize("change, message", [
    ("missing", "instance count"),
    ("duplicate_uid", "Duplicate CT SOP"),
    ("irregular", "Irregular CT slice spacing"),
    ("gantry_tilt", "Gantry tilt"),
])
def test_incomplete_or_unsupported_ct_is_rejected(pair, change, message):
    images, seg = pair
    if change == "missing":
        images = images[:-1]
    elif change == "duplicate_uid":
        images[1].SOPInstanceUID = images[0].SOPInstanceUID
    elif change == "irregular":
        images[2].ImagePositionPatient = [0, 0, 11]
    else:
        images[2].ImagePositionPatient = [1, 0, 10]
    with pytest.raises(ValidationError, match=message):
        convert(images, seg, 3)


def test_missing_spatial_flag_is_allowed_only_after_geometry_validation(pair):
    images, seg = pair
    for frame in seg.PerFrameFunctionalGroupsSequence:
        source = frame.DerivationImageSequence[0].SourceImageSequence[0]
        if "SpatialLocationsPreserved" in source:
            del source.SpatialLocationsPreserved
    _, masks, metadata = convert(images, seg, 3)
    assert metadata["checks"]["spatial_locations_flag_absent"] is True
    assert masks[:, 2, 2, 1].tolist() == [1, 1]


def test_patient_split_is_grouped_and_independent_of_record_order():
    records = [{"collection_id": "c4kc_kits", "patient_id": patient, "study": study}
               for patient, study in [("A", "1"), ("A", "2"), ("B", "3"), ("C", "4"), ("D", "5")]]
    first = split_patients(records, seed=2026)
    second = split_patients(list(reversed(records)), seed=2026)
    assignment = {record["patient_id"]: record["split"] for record in first}
    assert assignment == {record["patient_id"]: record["split"] for record in second}
    assert len({record["split"] for record in first if record["patient_id"] == "A"}) == 1
    assert sum(partition == "test" for partition in assignment.values()) == 1
    assert {record["patient_id"] for record in first if record["split"] == "train"}.isdisjoint(
        {record["patient_id"] for record in first if record["split"] == "test"})


def test_one_patient_cannot_form_train_and_test():
    with pytest.raises(ValidationError, match="At least two patient groups"):
        split_patients([{"collection_id": "c4kc_kits", "patient_id": "A"}])
