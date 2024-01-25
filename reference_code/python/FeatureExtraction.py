"""

"""

from typing import List

from pipeline_processor.core.data.data_node.abstract_image_node import AbstractImageNode
from pipeline_processor.core.data.data_node.mask_node.mask_node import MaskNode
from pipeline_processor.core.data.data_node.tensor_node import (
    TensorNode,
    TensorProperties,
)
from pipeline_processor.operators.features.intensity import Feature as IntensityFeature
from pipeline_processor.operators.features.shape import Feature as ShapeFeature
from py_pipeline import operators
from py_pipeline.core.pipe import Pipe


class FeatureExtraction(Pipe):
    """
    TODO:
    Subpipe that extracts both shape and intensity features (in the form of 2-dim matrix where rows
    represent labelled blob and columns represents label and required features of the blob.

    :var image: Input image ( `AbstractImageNode` ).
    :var mask: Input ccl mask (`MaskNode`) from which labels(blobs).
    """

    SHAPE_FEATURES = ShapeFeature
    INTENSITY_FEATURES = IntensityFeature

    def __init__(self):
        super().__init__()

        self.__image = self._add_input(name="image", node_type=AbstractImageNode)
        self.__mask = self._add_input(name="mask", node_type=MaskNode)

        self.__features = self._add_output(name="features", node_type=TensorNode)

        self.__shape_features = self._add_param("shape_features", List[ShapeFeature], required=True)
        self.__intensity_features = self._add_param(
            "intensity_features", List[IntensityFeature], required=True
        )

    def create_pipeline(self):
        shape_features = operators.features.Shape(self)
        shape_features.set_inputs(mask=self.__mask)
        shape_features.set_params(feature=self.__shape_features)
        shape_features.set_outputs(matrix="/shape_features")

        intensity_features = operators.features.Intensity(self)
        intensity_features.set_inputs(mask=self.__mask, image=self.__image)
        intensity_features.set_params(feature=self.__intensity_features)
        intensity_features.set_outputs(matrix="/intensity_features")

        append_features = operators.array.Manipulation(self)
        append_features.set_inputs(array="/shape_features", insert="/intensity_features")
        append_features.set_params(
            array_operation_type=append_features.ARRAY_OPERATION_TYPE.INSERT, axis=1
        )
        append_features.set_outputs(result="/merged_features")

        extracted_shape = operators.general.ExtractProperty(self)
        extracted_shape.set_inputs(node="/shape_features")
        extracted_shape.set_params(property_names=TensorProperties.SHAPE)
        extracted_shape.set_outputs(attributes="/shape_features/shape")

        number_of_column = operators.simple.iterable.Manipulation(self)
        number_of_column.set_inputs(node="/shape_features/shape")
        number_of_column.set_params(operation_type=number_of_column.OPERATION_TYPE.EXTRACT, index=1)
        number_of_column.set_outputs(data="/shape_features/shape/dim_1")

        remove_intensity_features_labels = operators.array.Manipulation(self)
        remove_intensity_features_labels.set_inputs(array="/merged_features")
        remove_intensity_features_labels.set_params(
            array_operation_type=remove_intensity_features_labels.ARRAY_OPERATION_TYPE.REMOVE,
            axis=1,
        )
        remove_intensity_features_labels.set_params_reference(index="/shape_features/shape/dim_1")
        remove_intensity_features_labels.set_outputs(result=self.__features)
