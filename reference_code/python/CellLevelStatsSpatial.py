from pipeline_processor.operators.array.reduce import ReductionType
from py_pipeline import operators
from py_pipeline.core import Pipe, special_params
from py_pipeline.operators.features.generation.spatial import DistanceType

# DISTANCE_TYPE = DistanceType.SIGNED_PSEUDODISTANCE
DISTANCE_TYPE = DistanceType.MATHEMATICAL_DISTANCE
TERMS_TO = ["Tumor", "Invasive Margin Midline", "CD8"]
STATISTICS = {
    "Mean Distance (µm)": (ReductionType.REGULAR.MEAN, None),
    "Median Distance (µm)": (ReductionType.REGULAR.MEDIAN, None),
    "25th Percentile Distance (µm)": (ReductionType.REGULAR.PERCENTILE, 25),
    "75th Percentile Distance (µm)": (ReductionType.REGULAR.PERCENTILE, 75),
    "Interquartile Range (µm)": (ReductionType.REGULAR.INTERQUARTILE_RANGE, None),
}


class SpatialStatistics(Pipe):
    """
    Author: Uroš Milivojević <uros@revealbio.com>
    Version: 3.0.0

    Distances are calculated for each target annotations in relation to the closest source annotation.
    Calculated distances are uploaded as properties for each target annotation and also reduced to
    calculate different statistics for the whole slide. Reduced statistics are uploaded as image
    properties.

    :var slide_path: Path to the WSI file.
    :var project_id: ID of a study on imageDx.
    :var image_id: ID of an image from the imageDx study specified by the `project_id`.
    """

    def __init__(self):
        super().__init__()

        # Special parameters.
        self.__slide_path = self._add_param(**special_params.slide_path)
        self.__project_id = self._add_param(**special_params.project_id)
        self.__image_id = self._add_param(**special_params.image_id)

    def create_pipeline(self):
        """
        Loads the slide, calculates spatial distances and uploads them to `imageDX`.
        """

        load_slide = operators.wsi.LoadSlide(self)
        load_slide.set_params_promotion(
            slide_path="slide_path", project_id="project_id", image_id="image_id"
        )
        load_slide.set_outputs(slide="/slide")

        SpatialStatistics.calculate(self)
        SpatialStatistics.upload_properties(self)

    @staticmethod
    def calculate(self, attachment=None):
        """
        Loads the annotations and calculates spatial statistics.
        """

        load_mpp = operators.general.ExtractProperty(self, attachment=attachment)
        load_mpp.set_inputs(node="/slide")
        load_mpp.set_params(property_names=load_mpp.PROPERTY_NAMES.SLIDE.MPP_AVG)
        load_mpp.set_outputs(attributes="/slide/mpp")

        for term in set(["CD8"] + TERMS_TO):
            load_annotations = operators.image_dx.annotations.Load(self)
            load_annotations.set_inputs(slide="/slide")
            load_annotations.set_params(
                annotation_type=load_annotations.ANNOTATION_TYPE.USER, terms=term
            )
            load_annotations.set_outputs(mask=term)

        SpatialStatistics.__delete_old_properties(self)

        cd8_to_centroids = operators.mask.general.ToCentroids(self)
        cd8_to_centroids.set_inputs(mask="/slide/CD8")
        cd8_to_centroids.set_outputs(mask="/slide/CD8")

        for term in TERMS_TO:
            spatial_statistics = operators.features.generation.Spatial(self)
            if term != "CD8":
                spatial_statistics.set_inputs(source="/slide/" + term, target="/slide/CD8")
                spatial_statistics.set_params(distance_type=DISTANCE_TYPE)
            else:
                spatial_statistics.set_inputs(source="/slide/" + term)
                spatial_statistics.set_params(
                    distance_type=spatial_statistics.DISTANCE_TYPE.MATHEMATICAL_DISTANCE
                )
            spatial_statistics.set_params_reference(mpp="/slide/mpp")
            spatial_statistics.set_outputs(features="/slide/" + term + "/features")

    @staticmethod
    def __delete_old_properties(self):
        """
        Deletes old properties before uploading new ones.
        """

        slide_property_names = []

        for term in TERMS_TO:
            for name in STATISTICS:
                slide_property_names.append("CD8 to " + term + ": " + name)

        delete_properties = operators.image_dx.properties.Delete(self)
        delete_properties.set_inputs(slide="/slide")
        delete_properties.set_params(type=delete_properties.TYPE.IMAGE, names=slide_property_names)

        annotation_property_names = []

        for term in TERMS_TO:
            annotation_property_names.append("CD8 to " + term + " : Distance to Nearest (µm)")

        extract_id = operators.general.ExtractProperty(self)
        extract_id.set_inputs(node="/slide/CD8")
        extract_id.set_params(property_names=extract_id.PROPERTY_NAMES.MASK.LABELS)
        extract_id.set_outputs(attributes="/cd8_labels")

        delete_properties = operators.image_dx.properties.Delete(self)
        delete_properties.set_inputs(slide="/slide")
        delete_properties.set_params(
            type=delete_properties.TYPE.ANNOTATION, names=annotation_property_names
        )
        delete_properties.set_params_reference(ids="/cd8_labels")

    @staticmethod
    def upload_properties(self):
        """ """

        empty_mask = operators.general.ExtractProperty(self)
        empty_mask.set_inputs(node="/slide/CD8")
        empty_mask.set_params(property_names=empty_mask.PROPERTY_NAMES.MASK.IS_EMPTY)
        empty_mask.set_outputs(attributes="/empty_mask")

        if_else = operators.branching.IfElse(self)
        if_else.set_inputs(flag="/empty_mask")

        SpatialStatistics.upload_slide_properties(self, attachment=(if_else, False))
        ann_properties = SpatialStatistics.upload_annotation_properties(self)

        return operators.branching.Join(self, [(if_else, True), ann_properties])

    @staticmethod
    def upload_slide_properties(self, attachment=None):
        """
        Reduce calculated distances, and upload those results as image properties.
        """

        for term in TERMS_TO:
            empty_mask = operators.general.ExtractProperty(self, attachment=attachment)
            empty_mask.set_inputs(node="/slide/" + term)
            empty_mask.set_params(property_names=empty_mask.PROPERTY_NAMES.MASK.IS_EMPTY)
            empty_mask.set_outputs(attributes="/empty_mask")

            if attachment is not None:
                attachment = None

            if_else = operators.branching.IfElse(self)
            if_else.set_inputs(flag="/empty_mask")

            remove_ids = operators.array.Manipulation(self, attachment=(if_else, False))
            remove_ids.set_inputs(array="/slide/" + term + "/features")
            remove_ids.set_params(
                array_operation_type=remove_ids.ARRAY_OPERATION_TYPE.REMOVE, index=0, axis=1
            )
            remove_ids.set_outputs(result="/slide/" + term + "/features/without_ids")

            for name, (stat, value) in STATISTICS.items():
                reduce_stat = operators.array.Reduce(self)
                reduce_stat.set_inputs(array="/slide/" + term + "/features/without_ids")
                reduce_stat.set_params(reduction_type=stat, axis=0)
                if value is not None:
                    reduce_stat.set_params(value=value)
                reduce_stat.set_outputs(result="/stat")

                upload_slide_properties = operators.image_dx.properties.Upload(self)
                upload_slide_properties.set_inputs(slide="/slide", properties="/stat")
                upload_slide_properties.set_params(
                    override=True,
                    names=["CD8 to " + term + ": " + name],
                    type=upload_slide_properties.TYPE.IMAGE,
                    dont_send=True,
                )

            operators.branching.Join(self, [(if_else, True), upload_slide_properties])

        operators.image_dx.properties.Flush(self)

    @staticmethod
    def upload_annotation_properties(self):
        """TODO"""

        for term in TERMS_TO:
            empty_mask = operators.general.ExtractProperty(self)
            empty_mask.set_inputs(node="/slide/" + term)
            empty_mask.set_params(property_names=empty_mask.PROPERTY_NAMES.MASK.IS_EMPTY)
            empty_mask.set_outputs(attributes="/empty_mask")

            if_else = operators.branching.IfElse(self)
            if_else.set_inputs(flag="/empty_mask")

            extract_property_values = operators.array.Manipulation(
                self, attachment=(if_else, False)
            )
            extract_property_values.set_inputs(array="/slide/" + term + "/features")
            extract_property_values.set_params(
                array_operation_type=extract_property_values.ARRAY_OPERATION_TYPE.EXTRACT,
                index=0,
                axis=1,
            )
            extract_property_values.set_outputs(result="/slide/" + term + "/features/ids")

            extract_property_values = operators.array.Manipulation(self)
            extract_property_values.set_inputs(array="/slide/" + term + "/features")
            extract_property_values.set_params(
                array_operation_type=extract_property_values.ARRAY_OPERATION_TYPE.EXTRACT,
                index=1,
                axis=1,
            )
            extract_property_values.set_outputs(result="/slide/" + term + "/features/values")

            convert_ids_to_list = operators.conversion.CastList(self)
            convert_ids_to_list.set_inputs(data="/slide/" + term + "/features/ids")
            convert_ids_to_list.set_outputs(list_data="/slide/" + term + "/features/ids")

            convert_ids_to_int = operators.conversion.ConvertPrimitive(self)
            convert_ids_to_int.set_inputs(node="/slide/" + term + "/features/ids")
            convert_ids_to_int.set_params(output_type=convert_ids_to_int.OUTPUT_TYPE.INTEGER)
            convert_ids_to_int.set_outputs(node="/slide/" + term + "/features/ids")

            upload_properties = operators.image_dx.properties.Upload(self)
            upload_properties.set_inputs(
                slide="/slide", properties="/slide/" + term + "/features/values"
            )
            upload_properties.set_params_reference(ids="/slide/" + term + "/features/ids")
            upload_properties.set_params(
                override=True,
                names=[
                    "CD8 to " + term + " : Distance to Nearest (µm)",
                ],
                type=upload_properties.TYPE.ANNOTATION,
                dont_send=True,
                one_to_one=True,
            )

            operators.branching.Join(self, [(if_else, True), upload_properties])

        flush = operators.image_dx.properties.Flush(self)

        return flush
