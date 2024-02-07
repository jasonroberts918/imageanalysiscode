"""
Module that calculates and uploads various tumor, stroma and invasive margin statistics.
"""

import numpy as np
from pipeline_processor.operators.mask.general.iterator import Mode
from py_pipeline import operators
from py_pipeline.core import Pipe, special_params

TISSUE_TERMS = "Tissue"
TUMOR_TERMS = "Tumor"
STROMA_TERMS = "Stroma"
INVASIVE_MARGIN_TERMS = "Invasive Margin"
CD8_TERMS = "CD8"


class RegularStatistics(Pipe):

    Pipeline that computes the following statistics for tumor, stroma and invasive margin: area (
    μm^2), CD8+ nuclei area (μm^2), CD8+ nuclei count, CD8+ nuclei % area (%), and CD8+ nuclei
    density (nuclei/mm^2) for each tumor, stroma and invasive margin region, and the same
    statistics for the entire tumor, stroma, invasive margin, tumor+stroma and
    tumor+stroma+invasive margin on the slide. It determines the tumor-stroma ratio, tissue area,
    and the class (inflamed, desert, or excluded).

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
        Pipeline that loads the slide, calculates tumor, stroma and invasive margin statistics,
        and uploads them.
        """

        load_slide = operators.wsi.LoadSlide(self)
        load_slide.set_params_promotion(
            slide_path="slide_path", project_id="project_id", image_id="image_id"
        )
        load_slide.set_outputs(slide="/slide")

        RegularStatistics.calculate(self)

    @staticmethod
    def calculate(self, attachment=None):
        """
        Block of operators that perform tumor, stroma, and invasive margin statistics calculations.

        :arg attachment: Variable used for branching, or merging after branching.

        :return: Variable used for merging after branching.
        """

        RegularStatistics.__delete_properties(self, attachment=attachment)

        RegularStatistics.__extract_pixel_size(self)
        RegularStatistics.__load_cd8_annotations(self)

        RegularStatistics.__set_parameters_tumor(self)
        RegularStatistics.__load_region_annotations(self)
        calculate_region_statistics = RegularStatistics.__calculate_region_statistics(self)
        RegularStatistics.__get_results_tumor(self, attachment=calculate_region_statistics)

        RegularStatistics.__set_parameters_stroma(self)

        if_else_tumor = operators.branching.IfElse(self)
        if_else_tumor.set_inputs(flag="/tumor_flag")

        reduce_nuclei = RegularStatistics.__reduce_nuclei(self, attachment=(if_else_tumor, True))

        join_tumor = operators.branching.Join(
            self,
            [
                reduce_nuclei,
                if_else_tumor,
            ],
        )

        RegularStatistics.__load_region_annotations(self, attachment=join_tumor)
        calculate_region_statistics = RegularStatistics.__calculate_region_statistics(self)
        RegularStatistics.__get_results_stroma(self, attachment=calculate_region_statistics)

        if_else_tumor = operators.branching.IfElse(self)
        if_else_tumor.set_inputs(flag="/tumor_flag")

        recover_nuclei = RegularStatistics.__recover_nuclei(self, attachment=(if_else_tumor, True))

        join_tumor = operators.branching.Join(
            self,
            [
                recover_nuclei,
                if_else_tumor,
            ],
        )

        calculate_tumor_plus_stroma_statistics = (
            RegularStatistics.__calculate_tumor_plus_stroma_statistics(self, attachment=join_tumor)
        )
        RegularStatistics.__set_parameters_tumor_plus_stroma(
            self, attachment=calculate_tumor_plus_stroma_statistics
        )
        RegularStatistics.__upload_tumor_plus_stroma_statistics(self)

        RegularStatistics.__set_parameters_invasive_margin(self)
        RegularStatistics.__load_region_annotations(self)

        extract_annotation_count = operators.general.ExtractProperty(self)
        extract_annotation_count.set_params(
            property_names=extract_annotation_count.PROPERTY_NAMES.MASK.COUNT
        )
        extract_annotation_count.set_inputs(node="/slide/region_ccl_mask")
        extract_annotation_count.set_outputs(attributes="/slide/annotation_count")

        invasive_margin = operators.simple.numeric.Compare(self)
        invasive_margin.set_params(compare_type=invasive_margin.COMPARE_TYPE.NOT_EQUAL, value=0)
        invasive_margin.set_inputs(datum="/slide/annotation_count")
        invasive_margin.set_outputs(result="/invasive_margin_flag")

        if_else_invasive_margin_flag = operators.branching.IfElse(self)
        if_else_invasive_margin_flag.set_inputs(flag="/invasive_margin_flag")

        calculate_region_statistics = RegularStatistics.__calculate_region_statistics(
            self, attachment=(if_else_invasive_margin_flag, True)
        )
        RegularStatistics.__get_results_invasive_margin(
            self, attachment=calculate_region_statistics
        )

        RegularStatistics.__load_overlapping_region_annotations(self)
        calculate_overlapping_region_statistics = (
            RegularStatistics.__calculate_overlapping_region_statistics(self)
        )
        RegularStatistics.__get_results_overlapping(
            self, attachment=calculate_overlapping_region_statistics
        )

        RegularStatistics.__calculate_tumor_plus_stroma_plus_invasive_margin_statistics(self)
        RegularStatistics.__set_parameters_tumor_plus_stroma_plus_invasive_margin(self)
        upload_tumor_plus_stroma_plus_invasive_margin_statistics = (
            RegularStatistics.__upload_tumor_plus_stroma_plus_invasive_margin_statistics(self)
        )

        join_invasive_margin = operators.branching.Join(
            self,
            [
                upload_tumor_plus_stroma_plus_invasive_margin_statistics,
                if_else_invasive_margin_flag,
            ],
        )

        operators.image_dx.properties.Flush(self, join_invasive_margin)

        join_tumor_cd8_percent = RegularStatistics.__classify_slide(self)

        RegularStatistics.__load_tissue_mask(self, attachment=join_tumor_cd8_percent)
        RegularStatistics.__calculate_region_area(self)
        upload = RegularStatistics.__upload_statistics_per_tissue(self)

        return upload

    @staticmethod
    def __delete_properties(self, attachment=None):
        """
        Block of operators that delete old properties if they exist.

        :arg attachment: Variable used for branching, or merging after branching.

        :return: Variable used for merging after branching.
        """
        delete_properties = operators.image_dx.properties.Delete(self, attachment=attachment)
        delete_properties.set_params(
            type=delete_properties.TYPE.IMAGE,
            names=[
                "Tumor: area (μm^2)",
                "Tumor: CD8 area (μm^2)",
                "Tumor: CD8 count",
                "Tumor: CD8 % area (%)",
                "Tumor: CD8 density (nuclei/mm^2)",
            ],
        )
        delete_properties.set_inputs(slide="/slide")

        delete_properties = operators.image_dx.properties.Delete(self)
        delete_properties.set_params(
            type=delete_properties.TYPE.IMAGE,
            names=[
                "Stroma: area (μm^2)",
                "Stroma: CD8 area (μm^2)",
                "Stroma: CD8 count",
                "Stroma: CD8 % area (%)",
                "Stroma: CD8 density (nuclei/mm^2)",
            ],
        )
        delete_properties.set_inputs(slide="/slide")

        delete_properties = operators.image_dx.properties.Delete(self)
        delete_properties.set_params(
            type=delete_properties.TYPE.IMAGE,
            names=[
                "Tumor : Stroma ratio",
            ],
        )
        delete_properties.set_inputs(slide="/slide")

        delete_properties = operators.image_dx.properties.Delete(self)
        delete_properties.set_params(
            type=delete_properties.TYPE.IMAGE,
            names=[
                "Tumor + Stroma: area (μm^2)",
                "Tumor + Stroma: CD8 area (μm^2)",
                "Tumor + Stroma: CD8 count",
                "Tumor + Stroma: CD8 % area (%)",
                "Tumor + Stroma: CD8 density (nuclei/mm^2)",
            ],
        )
        delete_properties.set_inputs(slide="/slide")

        delete_properties = operators.image_dx.properties.Delete(self)
        delete_properties.set_params(
            type=delete_properties.TYPE.IMAGE,
            names=[
                "Invasive Margin: area (μm^2)",
                "Invasive Margin: CD8 area (μm^2)",
                "Invasive Margin: CD8 count",
                "Invasive Margin: CD8 % area (%)",
                "Invasive Margin: CD8 density (nuclei/mm^2)",
            ],
        )
        delete_properties.set_inputs(slide="/slide")

        delete_properties = operators.image_dx.properties.Delete(self)
        delete_properties.set_params(
            type=delete_properties.TYPE.IMAGE,
            names=[
                "Tumor + Stroma + Invasive Margin: area (μm^2)",
                "Tumor + Stroma + Invasive Margin: CD8 area (μm^2)",
                "Tumor + Stroma + Invasive Margin: CD8 count",
                "Tumor + Stroma + Invasive Margin: CD8 % area (%)",
                "Tumor + Stroma + Invasive Margin: CD8 density (nuclei/mm^2)",
            ],
        )
        delete_properties.set_inputs(slide="/slide")

        delete_properties = operators.image_dx.properties.Delete(self)
        delete_properties.set_params(
            type=delete_properties.TYPE.IMAGE, names=["Inflammation Status"]
        )
        delete_properties.set_inputs(slide="/slide")
        delete_properties = operators.image_dx.properties.Delete(self)
        delete_properties.set_params(
            type=delete_properties.TYPE.IMAGE, names=["Tissue: area (μm^2)"]
        )
        delete_properties.set_inputs(slide="/slide")

        return delete_properties

    @staticmethod
    def __extract_pixel_size(self, attachment=None):
        """
        Block of operators that perform pixel width and height extraction.

        :arg attachment: Variable used for branching, or merging after branching.

        :return: Variable used for merging after branching.
        """

        extract_pixel_width_and_height = operators.general.ExtractProperty(
            self, attachment=attachment
        )
        extract_pixel_width_and_height.set_inputs(node="/slide")
        extract_pixel_width_and_height.set_params(
            property_names=extract_pixel_width_and_height.PROPERTY_NAMES.SLIDE.MPP
        )
        extract_pixel_width_and_height.set_outputs(attributes="/slide/pixel_width_and_height")

        extract_pixel_width = operators.simple.iterable.Manipulation(self)
        extract_pixel_width.set_inputs(iterable="/slide/pixel_width_and_height")
        extract_pixel_width.set_params(
            operation_type=extract_pixel_width.OPERATION_TYPE.EXTRACT, index=0
        )
        extract_pixel_width.set_outputs(result="/slide/pixel_width")

        extract_pixel_height = operators.simple.iterable.Manipulation(self)
        extract_pixel_height.set_inputs(iterable="/slide/pixel_width_and_height")
        extract_pixel_height.set_params(
            operation_type=extract_pixel_height.OPERATION_TYPE.EXTRACT, index=1
        )
        extract_pixel_height.set_outputs(result="/slide/pixel_height")

        return extract_pixel_height

    @staticmethod
    def __load_cd8_annotations(self, attachment=None):
        """
        Block of operators that loads CD8 annotations.

        :arg attachment: Variable used for branching, or merging after branching.

        :return: Variable used for merging after branching.
        """

        load_cd8_annotations = operators.image_dx.annotations.Load(self, attachment=attachment)
        load_cd8_annotations.set_inputs(slide="/slide")
        load_cd8_annotations.set_params(
            annotation_type=load_cd8_annotations.ANNOTATION_TYPE.USER,
            terms=CD8_TERMS,
        )
        load_cd8_annotations.set_params_promotion(project_id="project_id", image_id="image_id")
        load_cd8_annotations.set_outputs(mask="/slide/cd8_ccl_mask")

        to_centroids = operators.mask.general.ToCentroids(self)
        to_centroids.set_inputs(mask="/slide/cd8_ccl_mask")
        to_centroids.set_outputs(mask="/slide/cd8_term_ccl_mask_centroids")

        initialize_mask_labels = operators.array.Put(self)
        initialize_mask_labels.set_params(value=np.array([1]))
        initialize_mask_labels.set_outputs(tensor="/slide/region_cd8_ccl_mask_labels")

        return initialize_mask_labels

    @staticmethod
    def __set_parameters_tumor(self, attachment=None):
        """
        Block of operators that set parameters for tumor statistics calculation.

        :arg attachment: Variable used for branching, or merging after branching.

        :return: Variable used for merging after branching.
        """

        set_tumor_terms = operators.simple.general.Put(self, attachment=attachment)
        set_tumor_terms.set_params(value=TUMOR_TERMS)
        set_tumor_terms.set_outputs(data="/region_terms")

        set_tumor_region_statistics_names = operators.simple.general.Put(self)
        set_tumor_region_statistics_names.set_params(
            value=["Tumor: area (μm^2)", "Tumor: CD8 area (μm^2)", "Tumor: CD8 count"]
        )
        set_tumor_region_statistics_names.set_outputs(
            data="/statistics_per_region_names_area_cd8_area_cd8_count"
        )

        set_tumor_region_statistics_names = operators.simple.general.Put(self)
        set_tumor_region_statistics_names.set_params(
            value=["Tumor: CD8 % area (%)", "Tumor: CD8 " "density (nuclei/mm^2)"]
        )
        set_tumor_region_statistics_names.set_outputs(
            data="/statistics_per_region_names_cd8_percent_cd8_density"
        )

        set_tumor_slide_statistics_names = operators.simple.general.Put(self)
        set_tumor_slide_statistics_names.set_params(
            value=["Tumor: area (μm^2)", "Tumor: CD8 area (μm^2)", "Tumor: CD8 count"]
        )
        set_tumor_slide_statistics_names.set_outputs(
            data="/statistics_per_slide_names_area_cd8_area_cd8_count"
        )

        set_tumor_slide_statistics_names = operators.simple.general.Put(self)
        set_tumor_slide_statistics_names.set_params(
            value=["Tumor: CD8 % area (%)", "Tumor: CD8 density (nuclei/mm^2)"]
        )
        set_tumor_slide_statistics_names.set_outputs(
            data="/statistics_per_slide_names_cd8_percent_cd8_density"
        )

        return set_tumor_slide_statistics_names

    @staticmethod
    def __load_region_annotations(self, attachment=None):
        """
        Block of operators that load tumor, stroma or invasive margin annotations.

        :arg attachment: Variable used for branching, or merging after branching.

        :return: Variable used for merging after branching.
        """

        load_region_annotations = operators.image_dx.annotations.Load(self, attachment=attachment)
        load_region_annotations.set_inputs(slide="/slide")
        load_region_annotations.set_params_promotion(project_id="project_id", image_id="image_id")
        load_region_annotations.set_params_reference(terms="/region_terms")
        load_region_annotations.set_params(
            annotation_type=load_region_annotations.ANNOTATION_TYPE.USER
        )
        load_region_annotations.set_outputs(mask="/slide/region_ccl_mask")

        return load_region_annotations

    @staticmethod
    def __load_overlapping_region_annotations(self, attachment=None):
        """
        Block of operators that load tumor and stroma regions that overlap with the invasive
        margin annotations.

        :arg attachment: Variable used for branching, or merging after branching.

        :return: Variable used for merging after branching.
        """

        load_region_annotations = operators.image_dx.annotations.Load(self, attachment=attachment)
        load_region_annotations.set_inputs(slide="/slide")
        load_region_annotations.set_params_promotion(project_id="project_id", image_id="image_id")
        load_region_annotations.set_params(
            terms=[TUMOR_TERMS, STROMA_TERMS],
            annotation_type=load_region_annotations.ANNOTATION_TYPE.USER,
        )
        load_region_annotations.set_outputs(mask="/slide/tumor_stroma_ccl_mask")

        load_region_annotations = operators.image_dx.annotations.Load(self)
        load_region_annotations.set_inputs(slide="/slide")
        load_region_annotations.set_params_promotion(project_id="project_id", image_id="image_id")
        load_region_annotations.set_params(
            terms=INVASIVE_MARGIN_TERMS,
            annotation_type=load_region_annotations.ANNOTATION_TYPE.USER,
        )
        load_region_annotations.set_outputs(mask="/slide/invasive_margin_ccl_mask")

        generate_overlapping_region_mask = operators.mask.filtering.Intersection(self)
        generate_overlapping_region_mask.set_params(
            crop=True,
            threshold_type=generate_overlapping_region_mask.THRESHOLD_TYPE.AREA,
            threshold=1.0,
        )
        generate_overlapping_region_mask.set_inputs(
            mask="/slide/tumor_stroma_ccl_mask", filter_region="/slide/invasive_margin_ccl_mask"
        )
        generate_overlapping_region_mask.set_outputs(filtered="/slide/region_mask")

        return generate_overlapping_region_mask

    @staticmethod
    def __calculate_region_statistics(self, attachment=None):
        """
        Block of operators that calculate statistics for each tumor, stroma, or invasive margin
        region.

        :arg attachment: Variable used for branching, or merging after branching.

        :return: Variable used for merging after branching.
        """

        extract_annotation_count = operators.general.ExtractProperty(self, attachment=attachment)
        extract_annotation_count.set_params(
            property_names=extract_annotation_count.PROPERTY_NAMES.MASK.COUNT
        )
        extract_annotation_count.set_inputs(node="/slide/region_ccl_mask")
        extract_annotation_count.set_outputs(attributes="/slide/annotation_count")

        region = operators.simple.numeric.Compare(self)
        region.set_params(compare_type=region.COMPARE_TYPE.NOT_EQUAL, value=0)
        region.set_inputs(datum="/slide/annotation_count")
        region.set_outputs(result="/region_flag")

        if_else_region = operators.branching.IfElse(self)
        if_else_region.set_inputs(flag="/region_flag")

        make_collection = operators.mask.general.MakeCollection(self, (if_else_region, True))
        make_collection.set_inputs(mask="/slide/region_ccl_mask")
        make_collection.set_outputs(mask="/slide/region_ccl_mask")

        iteration_over_region_labels = operators.mask.general.Iterator(self)
        iteration_over_region_labels.set_inputs(mask="/slide/region_ccl_mask")
        iteration_over_region_labels.set_params(mode=Mode.LABEL)
        iteration_over_region_labels.set_outputs(
            mask="/slide/region_mask", label="/slide/region_label"
        )

        RegularStatistics.__calculate_region_area(self)

        RegularStatistics.__generate_region_cd8_ccl_mask(self)

        RegularStatistics.__calculate_cd8_area_cd8_count(self)
        RegularStatistics.__calculate_statistics_per_region(self)

        aggregate_region_statistics = operators.array.Aggregator(self)
        aggregate_region_statistics.set_params(
            output_array_type=aggregate_region_statistics.OUTPUT_ARRAY_TYPE.SAME, axis=1
        )
        aggregate_region_statistics.set_inputs(array="/slide/region_area_cd8_area_cd8_count")
        aggregate_region_statistics.set_outputs(
            array="/slide/region_area_cd8_area_cd8_count_slide_matrix"
        )

        RegularStatistics.__calculate_statistics_per_slide(self)
        upload_statistics_per_slide = RegularStatistics.__upload_statistics_per_slide(self)

        RegularStatistics.__put_statistics_per_region(self, attachment=(if_else_region, False))

        upload_region_area_cd8_area_cd8_count_per_slide = operators.image_dx.properties.Upload(self)
        upload_region_area_cd8_area_cd8_count_per_slide.set_inputs(
            properties="/slide/region_area_cd8_area_cd8_count_slide"
        )
        upload_region_area_cd8_area_cd8_count_per_slide.set_params(
            type=upload_region_area_cd8_area_cd8_count_per_slide.TYPE.IMAGE, override=True
        )
        upload_region_area_cd8_area_cd8_count_per_slide.set_params_reference(
            names="/statistics_per_slide_names_area_cd8_area_cd8_count"
        )
        upload_region_area_cd8_area_cd8_count_per_slide.set_params_promotion(ids="image_id")

        join_region = operators.branching.Join(
            self, [upload_statistics_per_slide, upload_region_area_cd8_area_cd8_count_per_slide]
        )

        return join_region

    @staticmethod
    def __calculate_overlapping_region_statistics(self, attachment=None):
        """
        Block of operators that calculate overlapping region statistics.

        :arg attachment: Variable used for branching, or merging after branching.

        :return: Variable used for merging after branching.
        """

        extract_annotation_count = operators.general.ExtractProperty(self, attachment=attachment)
        extract_annotation_count.set_params(
            property_names=extract_annotation_count.PROPERTY_NAMES.MASK.COUNT
        )
        extract_annotation_count.set_inputs(node="/slide/region_mask")
        extract_annotation_count.set_outputs(attributes="/slide/annotation_count")

        region = operators.simple.numeric.Compare(self)
        region.set_params(compare_type=region.COMPARE_TYPE.NOT_EQUAL, value=0)
        region.set_inputs(datum="/slide/annotation_count")
        region.set_outputs(result="/region_flag")

        if_else_region = operators.branching.IfElse(self)
        if_else_region.set_inputs(flag="/region_flag")

        RegularStatistics.__calculate_region_area(self, attachment=(if_else_region, True))

        RegularStatistics.__generate_region_cd8_ccl_mask(self)

        RegularStatistics.__calculate_cd8_area_cd8_count(self)
        calculate_statistics_per_region = RegularStatistics.__calculate_statistics_per_region(self)

        RegularStatistics.__put_statistics_per_region(self, attachment=(if_else_region, False))

        put_statistics = operators.array.Put(self)
        put_statistics.set_params_reference(value="/slide/region_area_cd8_area_cd8_count_slide")
        put_statistics.set_outputs(tensor="/slide/region_area_cd8_area_cd8_count_t")

        join_calculate_and_put = operators.branching.Join(
            self, [calculate_statistics_per_region, put_statistics]
        )

        return join_calculate_and_put

    @staticmethod
    def __calculate_region_area(self, attachment=None):
        """
        Block of operators that extract the region area in pixels, convert it to μm^2, and cast
        it to an array.

        :arg attachment: Variable used for branching, or merging after branching.

        :return: Variable used for merging after branching.
        """

        extract_region_area_in_pixels = operators.general.ExtractProperty(
            self, attachment=attachment
        )
        extract_region_area_in_pixels.set_inputs(node="/slide/region_mask")
        extract_region_area_in_pixels.set_params(
            property_names=extract_region_area_in_pixels.PROPERTY_NAMES.MASK.AREA
        )
        extract_region_area_in_pixels.set_outputs(attributes="/slide/region_area")

        calculate_region_area_in_square_micrometers = operators.simple.numeric.Math(self)
        calculate_region_area_in_square_micrometers.set_params(
            operation_type=calculate_region_area_in_square_micrometers.OPERATION_TYPE.BINARY.MULTIPLICATION
        )
        calculate_region_area_in_square_micrometers.set_inputs(
            datum_1="/slide/region_area", datum_2="/slide/pixel_width"
        )
        calculate_region_area_in_square_micrometers.set_outputs(result="/slide/region_area")

        calculate_region_area_in_square_micrometers = operators.simple.numeric.Math(self)
        calculate_region_area_in_square_micrometers.set_params(
            operation_type=calculate_region_area_in_square_micrometers.OPERATION_TYPE.BINARY.MULTIPLICATION
        )
        calculate_region_area_in_square_micrometers.set_inputs(
            datum_1="/slide/region_area", datum_2="/slide/pixel_height"
        )
        calculate_region_area_in_square_micrometers.set_outputs(result="/slide/region_area")

        # cast to array
        put_empty_simple = operators.simple.general.Put(self)
        put_empty_simple.set_params(value=[])
        put_empty_simple.set_outputs(data="/slide/region_area_simple")

        insert_region_area = operators.simple.iterable.Manipulation(self)
        insert_region_area.set_inputs(iterable="/slide/region_area_simple")
        insert_region_area.set_params_reference(value="/slide/region_area")
        insert_region_area.set_params(
            operation_type=insert_region_area.OPERATION_TYPE.INSERT, index=0
        )
        insert_region_area.set_outputs(result="/slide/region_area_simple")

        cast_array_tensor = operators.conversion.CastArray(self)
        cast_array_tensor.set_params(node_type=cast_array_tensor.NODE_TYPE.TENSOR)
        cast_array_tensor.set_inputs(data="/slide/region_area_simple")
        cast_array_tensor.set_outputs(array="/slide/region_area_array")

        return cast_array_tensor

    @staticmethod
    def __calculate_cd8_area_cd8_count(self, attachment=None):
        """
        Block of operators that calculates CD8 area and CD8 count and cast it to array.

        :arg attachment: Variable used for branching, or merging after branching.

        :return: Variable used for merging after branching.
        """

        # calculate cd8 area
        extract_cd8_area_in_pixels = operators.general.ExtractProperty(self, attachment=attachment)
        extract_cd8_area_in_pixels.set_inputs(node="/slide/region_cd8_ccl_mask")
        extract_cd8_area_in_pixels.set_params(
            property_names=extract_cd8_area_in_pixels.PROPERTY_NAMES.MASK.AREA
        )
        extract_cd8_area_in_pixels.set_outputs(attributes="/slide/cd8_area")

        calculate_cd8_area_in_square_micrometers = operators.simple.numeric.Math(self)
        calculate_cd8_area_in_square_micrometers.set_params(
            operation_type=calculate_cd8_area_in_square_micrometers.OPERATION_TYPE.BINARY.MULTIPLICATION
        )
        calculate_cd8_area_in_square_micrometers.set_inputs(
            datum_1="/slide/cd8_area", datum_2="/slide/pixel_width"
        )
        calculate_cd8_area_in_square_micrometers.set_outputs(result="/slide/cd8_area")

        calculate_cd8_area_in_square_millimeters = operators.simple.numeric.Math(self)
        calculate_cd8_area_in_square_millimeters.set_params(
            operation_type=calculate_cd8_area_in_square_millimeters.OPERATION_TYPE.BINARY.MULTIPLICATION
        )
        calculate_cd8_area_in_square_millimeters.set_inputs(
            datum_1="/slide/cd8_area", datum_2="/slide/pixel_height"
        )
        calculate_cd8_area_in_square_millimeters.set_outputs(result="/slide/cd8_area")

        # calculate cd8 area
        calculate_cd8_area_in_square_millimeters = operators.general.ExtractProperty(self)
        calculate_cd8_area_in_square_millimeters.set_inputs(node="/slide/region_cd8_ccl_mask")
        calculate_cd8_area_in_square_millimeters.set_params(
            property_names=calculate_cd8_area_in_square_millimeters.PROPERTY_NAMES.MASK.COUNT
        )
        calculate_cd8_area_in_square_millimeters.set_outputs(attributes="/slide/cd8_count")

        # cast to array
        put_empty_simple = operators.simple.general.Put(self)
        put_empty_simple.set_params(value=[])
        put_empty_simple.set_outputs(data="/slide/cd8_area_cd8_count")

        insert_cd8_area = operators.simple.iterable.Manipulation(self)
        insert_cd8_area.set_inputs(iterable="/slide/cd8_area_cd8_count")
        insert_cd8_area.set_params_reference(value="/slide/cd8_area")
        insert_cd8_area.set_params(operation_type=insert_cd8_area.OPERATION_TYPE.INSERT, index=0)
        insert_cd8_area.set_outputs(result="/slide/cd8_area_cd8_count")

        insert_cd8_count = operators.simple.iterable.Manipulation(self)
        insert_cd8_count.set_inputs(iterable="/slide/cd8_area_cd8_count")
        insert_cd8_count.set_params_reference(value="/slide/cd8_count")
        insert_cd8_count.set_params(operation_type=insert_cd8_count.OPERATION_TYPE.INSERT, index=1)
        insert_cd8_count.set_outputs(result="/slide/cd8_area_cd8_count")

        cast_cd8_area_and_cd8_count = operators.conversion.CastArray(self)
        cast_cd8_area_and_cd8_count.set_params(
            node_type=cast_cd8_area_and_cd8_count.NODE_TYPE.TENSOR
        )
        cast_cd8_area_and_cd8_count.set_inputs(data="/slide/cd8_area_cd8_count")
        cast_cd8_area_and_cd8_count.set_outputs(array="/slide/cd8_area_cd8_count")

        return cast_cd8_area_and_cd8_count

    @staticmethod
    def __calculate_statistics_per_region(self, attachment=None):
        """
        Block of operators that calculate statistics for the whole tumor, stroma or invasive margin.

        :arg attachment: Variable used for branching, or merging after branching.

        :return: Variable used for merging after branching.
        """

        calculate_cd8_percent_and_cd8_density = operators.array.Math(self, attachment=attachment)
        calculate_cd8_percent_and_cd8_density.set_params(
            operation_type=calculate_cd8_percent_and_cd8_density.OPERATION_TYPE.BINARY.DIVISION
        )
        calculate_cd8_percent_and_cd8_density.set_inputs(
            array_1="/slide/cd8_area_cd8_count", array_2="/slide/region_area_array"
        )
        calculate_cd8_percent_and_cd8_density.set_outputs(array="/slide/cd8_percent_cd8_density")

        put_factors = operators.simple.general.Put(self)
        put_factors.set_params(value=[10**2, 10**6])
        put_factors.set_outputs(data="/slide/factor")

        cast_factors = operators.conversion.CastArray(self)
        cast_factors.set_params(node_type=cast_factors.NODE_TYPE.TENSOR)
        cast_factors.set_inputs(data="/slide/factor")
        cast_factors.set_outputs(array="/slide/region_area_factor_arr")

        correct_units = operators.array.Math(self)
        correct_units.set_params(operation_type=correct_units.OPERATION_TYPE.BINARY.MULTIPLICATION)
        correct_units.set_inputs(
            array_1="/slide/cd8_percent_cd8_density", array_2="/slide/region_area_factor_arr"
        )
        correct_units.set_outputs(array="/slide/cd8_percent_cd8_density")

        insert_region_area = operators.array.Manipulation(self)
        insert_region_area.set_params(
            axis=0, index=0, array_operation_type=insert_region_area.ARRAY_OPERATION_TYPE.INSERT
        )
        insert_region_area.set_inputs(
            array="/slide/cd8_area_cd8_count", insert="/slide/region_area_array"
        )
        insert_region_area.set_outputs(result="/slide/region_area_cd8_area_cd8_count_t")

        prepare_for_aggregation = operators.array.Manipulation(self)
        prepare_for_aggregation.set_params(
            array_operation_type=prepare_for_aggregation.ARRAY_OPERATION_TYPE.EXPAND_DIMS, axis=1
        )
        prepare_for_aggregation.set_inputs(array="/slide/region_area_cd8_area_cd8_count_t")
        prepare_for_aggregation.set_outputs(result="/slide/region_area_cd8_area_cd8_count")

        return prepare_for_aggregation

    @staticmethod
    def __put_statistics_per_region(self, attachment=None):
        """
        Block of operators that put statistics for the whole tumor, stroma, or invasive margin.

        :arg attachment: Variable used for branching, or merging after branching.

        :return: Variable used for merging after branching.
        """

        put_region_area_cd8_area_cd8_count_slide = operators.array.Put(self, attachment=attachment)
        put_region_area_cd8_area_cd8_count_slide.set_params(value=np.array([0, 0, 0]))
        put_region_area_cd8_area_cd8_count_slide.set_outputs(
            tensor="/slide/region_area_cd8_area_cd8_count_slide"
        )

        put_region_area_slide = operators.array.Put(self)
        put_region_area_slide.set_params(value=np.array([0]))
        put_region_area_slide.set_outputs(tensor="/slide/region_area_slide")

        put_region_cd8_percent_cd8_density_per_slide = operators.array.Put(self)
        put_region_cd8_percent_cd8_density_per_slide.set_params(value=np.array([0, 0]))
        put_region_cd8_percent_cd8_density_per_slide.set_outputs(
            tensor="/slide/cd8_percent_cd8_density_slide"
        )

        return put_region_cd8_percent_cd8_density_per_slide

    @staticmethod
    def __load_tissue_mask(self, attachment=None):
        """
        Block of operators that perform tissue mask loading and rescaling.

        :arg attachment: Variable used for branching, or merging after branching.

        :return: Variable used for merging after branching.
        """

        load_tissue_mask = operators.image_dx.annotations.Load(self, attachment=attachment)
        load_tissue_mask.set_inputs(slide="/slide")
        load_tissue_mask.set_params_promotion(
            project_id="project_id",
            image_id="image_id",
        )
        load_tissue_mask.set_params(
            annotation_type=load_tissue_mask.ANNOTATION_TYPE.USER, terms=TISSUE_TERMS
        )
        load_tissue_mask.set_outputs(mask="/slide/region_mask")

        return load_tissue_mask

    @staticmethod
    def __generate_region_cd8_ccl_mask(self, attachment=None):
        """
        Block of operators that generate an intersection mask of the CD8 ccl mask and the tumor,
        stroma, or invasive margin mask.

        :arg attachment: Variable used for branching, or merging after branching.

        :return: Variable used for merging after branching.
        """

        generate_cd8_annotations_region_mask_centroids = operators.mask.filtering.FastIntersection(
            self, attachment=attachment
        )
        generate_cd8_annotations_region_mask_centroids.set_params(
            query_predicate=generate_cd8_annotations_region_mask_centroids.QUERY_PREDICATE.INTERSECTS
        )
        generate_cd8_annotations_region_mask_centroids.set_inputs(
            mask="/slide/cd8_term_ccl_mask_centroids", intersection_region="/slide/region_mask"
        )
        generate_cd8_annotations_region_mask_centroids.set_outputs(
            filtered_mask="/slide/region_cd8_ccl_mask_centroids"
        )

        extract_labels = operators.general.ExtractProperty(self)
        extract_labels.set_params(property_names=extract_labels.PROPERTY_NAMES.MASK.LABELS)
        extract_labels.set_inputs(node="/slide/region_cd8_ccl_mask_centroids")
        extract_labels.set_outputs(attributes="/slide/region_cd8_ccl_mask_labels")

        generate_cd8_annotations_region_mask = operators.mask.filtering.Labels(self)
        generate_cd8_annotations_region_mask.set_params(
            operation_type=generate_cd8_annotations_region_mask.OPERATION_TYPE.INCLUDE
        )
        generate_cd8_annotations_region_mask.set_params_reference(
            labels="/slide/region_cd8_ccl_mask_labels"
        )
        generate_cd8_annotations_region_mask.set_inputs(mask="/slide/cd8_ccl_mask")
        generate_cd8_annotations_region_mask.set_outputs(mask="/slide/region_cd8_ccl_mask")

        return generate_cd8_annotations_region_mask

    @staticmethod
    def __calculate_statistics_per_slide(self, attachment=None):
        """
        Block of operators that calculate statistics for the whole slide.

        :arg attachment: Variable used for branching, or merging after branching.

        :return: Variable used for merging after branching.
        """

        sum_additive_statistics = operators.array.Reduce(self, attachment=attachment)
        sum_additive_statistics.set_params(
            axis=1, reduction_type=sum_additive_statistics.REDUCTION_TYPE.REGULAR.SUM
        )
        sum_additive_statistics.set_inputs(
            array="/slide/region_area_cd8_area_cd8_count_slide_matrix"
        )
        sum_additive_statistics.set_outputs(result="/slide/region_area_cd8_area_cd8_count_slide")

        extract_region_area_per_slide = operators.array.Manipulation(self)
        extract_region_area_per_slide.set_params(
            array_operation_type=extract_region_area_per_slide.ARRAY_OPERATION_TYPE.EXTRACT,
            index=[0],
            axis=0,
        )
        extract_region_area_per_slide.set_inputs(
            array="/slide/region_area_cd8_area_cd8_count_slide"
        )
        extract_region_area_per_slide.set_outputs(result="/slide/region_area_slide")

        remove_region_area = operators.array.Manipulation(self)
        remove_region_area.set_params(
            array_operation_type=remove_region_area.ARRAY_OPERATION_TYPE.REMOVE, index=0, axis=0
        )
        remove_region_area.set_inputs(array="/slide/region_area_cd8_area_cd8_count_slide")
        remove_region_area.set_outputs(result="/slide/cd8_area_cd8_count_slide")

        calculate_cd8_percent_cd8_density_per_slide = operators.array.Math(self)
        calculate_cd8_percent_cd8_density_per_slide.set_params(
            operation_type=calculate_cd8_percent_cd8_density_per_slide.OPERATION_TYPE.BINARY.DIVISION
        )
        calculate_cd8_percent_cd8_density_per_slide.set_inputs(
            array_1="/slide/cd8_area_cd8_count_slide", array_2="/slide/region_area_slide"
        )
        calculate_cd8_percent_cd8_density_per_slide.set_outputs(
            array="/slide/cd8_percent_cd8_density_slide"
        )

        put_factors = operators.simple.general.Put(self)
        put_factors.set_params(value=[10**2, 10**6])
        put_factors.set_outputs(data="/slide/factor")

        cast_factors = operators.conversion.CastArray(self)
        cast_factors.set_params(node_type=cast_factors.NODE_TYPE.TENSOR)
        cast_factors.set_inputs(data="/slide/factor")
        cast_factors.set_outputs(array="/slide/factor_array")

        correct_units = operators.array.Math(self)
        correct_units.set_params(operation_type=correct_units.OPERATION_TYPE.BINARY.MULTIPLICATION)
        correct_units.set_inputs(
            array_1="/slide/cd8_percent_cd8_density_slide", array_2="/slide/factor_array"
        )
        correct_units.set_outputs(array="/slide/cd8_percent_cd8_density_slide")

        return correct_units

    @staticmethod
    def __upload_statistics_per_slide(self, attachment=None):
        """
        Block of operators that upload statistics for the whole slide.

        :arg attachment: Variable used for branching, or merging after branching.

        :return: Variable used for merging after branching.
        """

        upload_region_area_cd8_area_cd8_count_per_slide = operators.image_dx.properties.Upload(
            self, attachment=attachment
        )
        upload_region_area_cd8_area_cd8_count_per_slide.set_inputs(
            properties="/slide/region_area_cd8_area_cd8_count_slide"
        )
        upload_region_area_cd8_area_cd8_count_per_slide.set_params(
            type=upload_region_area_cd8_area_cd8_count_per_slide.TYPE.IMAGE, override=True
        )
        upload_region_area_cd8_area_cd8_count_per_slide.set_params_reference(
            names="/statistics_per_slide_names_area_cd8_area_cd8_count"
        )
        upload_region_area_cd8_area_cd8_count_per_slide.set_params_promotion(ids="image_id")

        upload_cd8_percent_cd8_density_per_slide = operators.image_dx.properties.Upload(self)
        upload_cd8_percent_cd8_density_per_slide.set_inputs(
            properties="/slide/cd8_percent_cd8_density_slide"
        )
        upload_cd8_percent_cd8_density_per_slide.set_params(
            type=upload_cd8_percent_cd8_density_per_slide.TYPE.IMAGE,
            override=True,
        )
        upload_cd8_percent_cd8_density_per_slide.set_params_reference(
            names="/statistics_per_slide_names_cd8_percent_cd8_density"
        )
        upload_cd8_percent_cd8_density_per_slide.set_params_promotion(ids="image_id")

        return upload_cd8_percent_cd8_density_per_slide

    @staticmethod
    def __set_parameters_stroma(self, attachment=None):
        """
        Block of operators that set parameters for stroma statistics calculation.

        :arg attachment: Variable used for branching, or merging after branching.

        :return: Variable used for merging after branching.
        """

        set_stroma_terms = operators.simple.general.Put(self, attachment=attachment)
        set_stroma_terms.set_params(value=STROMA_TERMS)
        set_stroma_terms.set_outputs(data="/region_terms")

        set_stroma_region_statistics_names = operators.simple.general.Put(self)
        set_stroma_region_statistics_names.set_params(
            value=["Stroma: area (μm^2)", "Stroma: CD8 area (μm^2)", "Stroma: CD8 count"]
        )
        set_stroma_region_statistics_names.set_outputs(
            data="/statistics_per_region_names_area_cd8_area_cd8_count"
        )

        set_stroma_region_statistics_names = operators.simple.general.Put(self)
        set_stroma_region_statistics_names.set_params(
            value=["Stroma: CD8 % area (%)", "Stroma: CD8 density (nuclei/mm^2)"]
        )
        set_stroma_region_statistics_names.set_outputs(
            data="/statistics_per_region_names_cd8_percent_cd8_density"
        )

        set_stroma_slide_statistics_names = operators.simple.general.Put(self)
        set_stroma_slide_statistics_names.set_params(
            value=["Stroma: area (μm^2)", "Stroma: CD8 area (μm^2)", "Stroma: CD8 count"]
        )
        set_stroma_slide_statistics_names.set_outputs(
            data="/statistics_per_slide_names_area_cd8_area_cd8_count"
        )

        set_stroma_slide_statistics_names = operators.simple.general.Put(self)
        set_stroma_slide_statistics_names.set_params(
            value=["Stroma: CD8 % area (%)", "Stroma: CD8 density (nuclei/mm^2)"]
        )
        set_stroma_slide_statistics_names.set_outputs(
            data="/statistics_per_slide_names_cd8_percent_cd8_density"
        )

        return set_stroma_slide_statistics_names

    @staticmethod
    def __set_parameters_invasive_margin(self, attachment=None):
        """
        Block of operators that set parameters for invasive margin statistics calculation.

        :arg attachment: Variable used for branching, or merging after branching.

        :return: Variable used for merging after branching.
        """

        set_invasive_margin_terms = operators.simple.general.Put(self, attachment=attachment)
        set_invasive_margin_terms.set_params(value=INVASIVE_MARGIN_TERMS)
        set_invasive_margin_terms.set_outputs(data="/region_terms")

        set_invasive_margin_region_statistics_names = operators.simple.general.Put(self)
        set_invasive_margin_region_statistics_names.set_params(
            value=[
                "Invasive Margin: area (μm^2)",
                "Invasive Margin: CD8 area (μm^2)",
                "Invasive Margin: CD8 count",
            ]
        )
        set_invasive_margin_region_statistics_names.set_outputs(
            data="/statistics_per_region_names_area_cd8_area_cd8_count"
        )

        set_invasive_margin_region_statistics_names = operators.simple.general.Put(self)
        set_invasive_margin_region_statistics_names.set_params(
            value=["Invasive Margin: CD8 % area (%)", "Invasive Margin: CD8 density (nuclei/mm^2)"]
        )
        set_invasive_margin_region_statistics_names.set_outputs(
            data="/statistics_per_region_names_cd8_percent_cd8_density"
        )

        set_invasive_margin_slide_statistics_names = operators.simple.general.Put(self)
        set_invasive_margin_slide_statistics_names.set_params(
            value=[
                "Invasive Margin: area (μm^2)",
                "Invasive Margin: CD8 area (μm^2)",
                "Invasive Margin: CD8 count",
            ]
        )
        set_invasive_margin_slide_statistics_names.set_outputs(
            data="/statistics_per_slide_names_area_cd8_area_cd8_count"
        )

        set_invasive_margin_slide_statistics_names = operators.simple.general.Put(self)
        set_invasive_margin_slide_statistics_names.set_params(
            value=["Invasive Margin: CD8 % area (%)", "Invasive Margin: CD8 density (nuclei/mm^2)"]
        )
        set_invasive_margin_slide_statistics_names.set_outputs(
            data="/statistics_per_slide_names_cd8_percent_cd8_density"
        )

        return set_invasive_margin_slide_statistics_names

    @staticmethod
    def __get_results_tumor(self, attachment=None):
        """
        Block of operators that get the result of the tumor statistics calculation.

        :arg attachment: Variable used for branching, or merging after branching.

        :return: Variable used for merging after branching.
        """

        get_tumor_area_cd8_area_cd8_count_per_slide = operators.array.Put(
            self, attachment=attachment
        )
        get_tumor_area_cd8_area_cd8_count_per_slide.set_params_reference(
            value="/slide/region_area_cd8_area_cd8_count_slide"
        )
        get_tumor_area_cd8_area_cd8_count_per_slide.set_outputs(
            tensor="/slide/tumor_area_cd8_area_cd8_count_slide"
        )

        get_tumor_area_per_slide = operators.array.Put(self)
        get_tumor_area_per_slide.set_params_reference(value="/slide/region_area_slide")
        get_tumor_area_per_slide.set_outputs(tensor="/slide/tumor_area_slide")

        get_tumor_cd8_percent_cd8_density_per_slide = operators.array.Put(self)
        get_tumor_cd8_percent_cd8_density_per_slide.set_params_reference(
            value="/slide/cd8_percent_cd8_density_slide"
        )
        get_tumor_cd8_percent_cd8_density_per_slide.set_outputs(
            tensor="/slide/tumor_cd8_percent_cd8_density_slide"
        )

        get_tumor_area_simople_per_slide = operators.array.Manipulation(self)
        get_tumor_area_simople_per_slide.set_params(
            array_operation_type=get_tumor_area_simople_per_slide.ARRAY_OPERATION_TYPE.EXTRACT,
            index=0,
            axis=0,
        )
        get_tumor_area_simople_per_slide.set_inputs(
            array="/slide/region_area_cd8_area_cd8_count_slide"
        )
        get_tumor_area_simople_per_slide.set_outputs(result="/slide/tumor_area_simple_slide")

        get_tumor_cd8_percent_per_slide = operators.array.Manipulation(self)
        get_tumor_cd8_percent_per_slide.set_params(
            array_operation_type=get_tumor_cd8_percent_per_slide.ARRAY_OPERATION_TYPE.EXTRACT,
            index=0,
            axis=0,
        )
        get_tumor_cd8_percent_per_slide.set_inputs(
            array="/slide/tumor_cd8_percent_cd8_density_slide"
        )
        get_tumor_cd8_percent_per_slide.set_outputs(result="/slide/tumor_cd8_percent_slide")

        get_tumor_flag = operators.general.DuplicateNode(self)
        get_tumor_flag.set_inputs(node="/region_flag")
        get_tumor_flag.set_outputs(duplicate="/tumor_flag")

        return get_tumor_cd8_percent_per_slide

    @staticmethod
    def __get_results_stroma(self, attachment=None):
        """
        Block of operators that get the result of the stroma statistics calculation.

        :arg attachment: Variable used for branching, or merging after branching.

        :return: Variable used for merging after branching.
        """

        get_stroma_area_cd8_area_cd8_count_per_slide = operators.array.Put(
            self, attachment=attachment
        )
        get_stroma_area_cd8_area_cd8_count_per_slide.set_params_reference(
            value="/slide/region_area_cd8_area_cd8_count_slide"
        )
        get_stroma_area_cd8_area_cd8_count_per_slide.set_outputs(
            tensor="/slide/stroma_area_cd8_area_cd8_count_slide"
        )

        get_stroma_area_per_slide = operators.array.Put(self)
        get_stroma_area_per_slide.set_params_reference(value="/slide/region_area_slide")
        get_stroma_area_per_slide.set_outputs(tensor="/slide/stroma_area_slide")

        get_stroma_area_simople_per_slide = operators.array.Manipulation(self)
        get_stroma_area_simople_per_slide.set_params(
            array_operation_type=get_stroma_area_simople_per_slide.ARRAY_OPERATION_TYPE.EXTRACT,
            index=0,
            axis=0,
        )
        get_stroma_area_simople_per_slide.set_inputs(
            array="/slide/region_area_cd8_area_cd8_count_slide"
        )
        get_stroma_area_simople_per_slide.set_outputs(result="/slide/stroma_area_simple_slide")

        return get_stroma_area_simople_per_slide

    @staticmethod
    def __get_results_invasive_margin(self, attachment=None):
        """
        Block of operators that get the result of the invasive margin statistics calculation.

        :arg attachment: Variable used for branching, or merging after branching.

        :return: Variable used for merging after branching.
        """

        get_invasive_margin_area_cd8_area_cd8_count_per_slide = operators.array.Put(
            self, attachment=attachment
        )
        get_invasive_margin_area_cd8_area_cd8_count_per_slide.set_params_reference(
            value="/slide/region_area_cd8_area_cd8_count_slide"
        )
        get_invasive_margin_area_cd8_area_cd8_count_per_slide.set_outputs(
            tensor="/slide/invasive_margin_area_cd8_area_cd8_count_slide"
        )

        return get_invasive_margin_area_cd8_area_cd8_count_per_slide

    @staticmethod
    def __get_results_overlapping(self, attachment=None):
        """
        Block of operators that get the result of the overlapping region statistics calculation.

        :arg attachment: Variable used for branching, or merging after branching.

        :return: Variable used for merging after branching.
        """

        get_invasive_margin_area_cd8_area_cd8_count_per_slide = operators.array.Put(
            self, attachment=attachment
        )
        get_invasive_margin_area_cd8_area_cd8_count_per_slide.set_params_reference(
            value="/slide/region_area_cd8_area_cd8_count_t"
        )
        get_invasive_margin_area_cd8_area_cd8_count_per_slide.set_outputs(
            tensor="/slide/overlapping_area_cd8_area_cd8_count_slide"
        )

        return get_invasive_margin_area_cd8_area_cd8_count_per_slide

    @staticmethod
    def __reduce_nuclei(self, attachment=None):
        """
        Block of operators that exclude already processed nuclei.

        :arg attachment: Variable used for branching, or merging after branching.

        :return: Variable used for merging after branching.
        """

        save_old = operators.general.DuplicateNode(self, attachment=attachment)
        save_old.set_inputs(node="/slide/cd8_term_ccl_mask_centroids")
        save_old.set_outputs(duplicate="/slide/cd8_term_ccl_mask_centroids_old")

        reduce_cd8_term_ccl_mask_centroids = operators.mask.filtering.Labels(self)
        reduce_cd8_term_ccl_mask_centroids.set_params(
            operation_type=reduce_cd8_term_ccl_mask_centroids.OPERATION_TYPE.EXCLUDE
        )
        reduce_cd8_term_ccl_mask_centroids.set_params_reference(
            labels="/slide/region_cd8_ccl_mask_labels"
        )
        reduce_cd8_term_ccl_mask_centroids.set_inputs(mask="/slide/cd8_term_ccl_mask_centroids")
        reduce_cd8_term_ccl_mask_centroids.set_outputs(mask="/slide/cd8_term_ccl_mask_centroids")

        return reduce_cd8_term_ccl_mask_centroids

    @staticmethod
    def __recover_nuclei(self, attachment=None):
        """
        Block of operators that recover the mask with all the nuclei.

        :arg attachment: Variable used for branching, or merging after branching.

        :return: Variable used for merging after branching.
        """

        recover_old = operators.general.DuplicateNode(self, attachment=attachment)
        recover_old.set_inputs(node="/slide/cd8_term_ccl_mask_centroids_old")
        recover_old.set_outputs(duplicate="/slide/cd8_term_ccl_mask_centroids")

        return recover_old

    @staticmethod
    def __calculate_tumor_plus_stroma_statistics(self, attachment=None):
        """
        Block of operators that calculate statistics for the whole tumor+stroma.

        :arg attachment: Variable used for branching, or merging after branching.

        :return: Variable used for merging after branching.
        """

        sum_additive_statistics_per_slide = operators.array.Math(self, attachment=attachment)
        sum_additive_statistics_per_slide.set_params(
            operation_type=sum_additive_statistics_per_slide.OPERATION_TYPE.BINARY.ADDITION
        )
        sum_additive_statistics_per_slide.set_inputs(
            array_1="/slide/tumor_area_cd8_area_cd8_count_slide",
            array_2="/slide/stroma_area_cd8_area_cd8_count_slide",
        )
        sum_additive_statistics_per_slide.set_outputs(
            array="/slide/tumor_plus_stroma_area_cd8_area_cd8_count_slide"
        )

        extract_area_per_slide = operators.array.Manipulation(self)
        extract_area_per_slide.set_params(
            array_operation_type=extract_area_per_slide.ARRAY_OPERATION_TYPE.EXTRACT,
            index=[0],
            axis=0,
        )
        extract_area_per_slide.set_inputs(
            array="/slide/tumor_plus_stroma_area_cd8_area_cd8_count_slide"
        )
        extract_area_per_slide.set_outputs(result="/slide/tumor_plus_stroma_area_slide")

        extract_cd8_area_and_cd8_count_per_slide = operators.array.Manipulation(self)
        extract_cd8_area_and_cd8_count_per_slide.set_params(
            array_operation_type=extract_cd8_area_and_cd8_count_per_slide.ARRAY_OPERATION_TYPE.REMOVE,
            index=0,
            axis=0,
        )
        extract_cd8_area_and_cd8_count_per_slide.set_inputs(
            array="/slide/tumor_plus_stroma_area_cd8_area_cd8_count_slide"
        )
        extract_cd8_area_and_cd8_count_per_slide.set_outputs(
            result="/slide/cd8_area_cd8_count_slide"
        )

        calculate_cd8_percent_and_cd8_density = operators.array.Math(self)
        calculate_cd8_percent_and_cd8_density.set_params(
            operation_type=calculate_cd8_percent_and_cd8_density.OPERATION_TYPE.BINARY.DIVISION
        )
        calculate_cd8_percent_and_cd8_density.set_inputs(
            array_1="/slide/cd8_area_cd8_count_slide", array_2="/slide/tumor_plus_stroma_area_slide"
        )
        calculate_cd8_percent_and_cd8_density.set_outputs(
            array="/slide/cd8_percent_cd8_density_slide"
        )

        put_factors = operators.simple.general.Put(self)
        put_factors.set_params(value=[10**2, 10**6])
        put_factors.set_outputs(data="/slide/factor")

        cast_factors = operators.conversion.CastArray(self)
        cast_factors.set_params(node_type=cast_factors.NODE_TYPE.TENSOR)
        cast_factors.set_inputs(data="/slide/factor")
        cast_factors.set_outputs(array="/slide/factor_array")

        correct_units = operators.array.Math(self)
        correct_units.set_params(operation_type=correct_units.OPERATION_TYPE.BINARY.MULTIPLICATION)
        correct_units.set_inputs(
            array_1="/slide/cd8_percent_cd8_density_slide", array_2="/slide/factor_array"
        )
        correct_units.set_outputs(array="/slide/cd8_percent_cd8_density_slide")

        compare_stroma_area = operators.simple.numeric.Compare(self)
        compare_stroma_area.set_params(
            compare_type=compare_stroma_area.COMPARE_TYPE.NOT_EQUAL, value=0.0
        )
        compare_stroma_area.set_inputs(datum="/slide/stroma_area_simple_slide")
        compare_stroma_area.set_outputs(result="/stroma_flag")

        if_else_stroma = operators.branching.IfElse(self)
        if_else_stroma.set_inputs(flag="/stroma_flag")

        calculate_ratio = operators.array.Math(self, (if_else_stroma, True))
        calculate_ratio.set_params(operation_type=calculate_ratio.OPERATION_TYPE.BINARY.DIVISION)
        calculate_ratio.set_inputs(
            array_1="/slide/tumor_area_slide", array_2="/slide/stroma_area_slide"
        )
        calculate_ratio.set_outputs(array="/slide/tumor_stroma_ratio")

        upload_tumor_plus_stroma_statistics_per_slide = operators.image_dx.properties.Upload(self)
        upload_tumor_plus_stroma_statistics_per_slide.set_inputs(
            properties="/slide/tumor_stroma_ratio"
        )
        upload_tumor_plus_stroma_statistics_per_slide.set_params(
            type=upload_tumor_plus_stroma_statistics_per_slide.TYPE.IMAGE,
            names=["Tumor : Stroma ratio"],
            override=True,
        )
        upload_tumor_plus_stroma_statistics_per_slide.set_params_promotion(ids="image_id")

        join_tumor_and_stroma = operators.branching.Join(
            self, [upload_tumor_plus_stroma_statistics_per_slide, if_else_stroma]
        )

        return join_tumor_and_stroma

    @staticmethod
    def __calculate_tumor_plus_stroma_plus_invasive_margin_statistics(self, attachment=None):
        """
        Block of operators that calculate statistics for the whole tumor+stroma+invasive margin.

        :arg attachment: Variable used for branching, or merging after branching.

        :return: Variable used for merging after branching.
        """

        sum_additive_statistics_per_slide = operators.array.Math(self, attachment=attachment)
        sum_additive_statistics_per_slide.set_params(
            operation_type=sum_additive_statistics_per_slide.OPERATION_TYPE.BINARY.ADDITION
        )
        sum_additive_statistics_per_slide.set_inputs(
            array_1="/slide/tumor_plus_stroma_area_cd8_area_cd8_count_slide",
            array_2="/slide/invasive_margin_area_cd8_area_cd8_count_slide",
        )
        sum_additive_statistics_per_slide.set_outputs(
            array="/slide/tumor_plus_stroma_plus_invasive_margin_area_cd8_area_cd8_count_slide"
        )

        subtract_statistics_for_overlapping_region_per_slide = operators.array.Math(self)
        subtract_statistics_for_overlapping_region_per_slide.set_params(
            operation_type=sum_additive_statistics_per_slide.OPERATION_TYPE.BINARY.SUBTRACTION
        )
        subtract_statistics_for_overlapping_region_per_slide.set_inputs(
            array_1="/slide/tumor_plus_stroma_plus_invasive_margin_area_cd8_area_cd8_count_slide",
            array_2="/slide/overlapping_area_cd8_area_cd8_count_slide",
        )
        subtract_statistics_for_overlapping_region_per_slide.set_outputs(
            array="/slide/tumor_plus_stroma_plus_invasive_margin_area_cd8_area_cd8_count_slide"
        )

        extract_area_per_slide = operators.array.Manipulation(self)
        extract_area_per_slide.set_params(
            array_operation_type=extract_area_per_slide.ARRAY_OPERATION_TYPE.EXTRACT,
            index=[0],
            axis=0,
        )
        extract_area_per_slide.set_inputs(
            array="/slide/tumor_plus_stroma_plus_invasive_margin_area_cd8_area_cd8_count_slide"
        )
        extract_area_per_slide.set_outputs(
            result="/slide/tumor_plus_stroma_plus_invasive_margin_area_slide"
        )

        extract_cd8_area_and_cd8_count_per_slide = operators.array.Manipulation(self)
        extract_cd8_area_and_cd8_count_per_slide.set_params(
            array_operation_type=extract_cd8_area_and_cd8_count_per_slide.ARRAY_OPERATION_TYPE.REMOVE,
            index=0,
            axis=0,
        )
        extract_cd8_area_and_cd8_count_per_slide.set_inputs(
            array="/slide/tumor_plus_stroma_plus_invasive_margin_area_cd8_area_cd8_count_slide"
        )
        extract_cd8_area_and_cd8_count_per_slide.set_outputs(
            result="/slide/cd8_area_cd8_count_slide"
        )

        calculate_cd8_percent_and_cd8_density = operators.array.Math(self)
        calculate_cd8_percent_and_cd8_density.set_params(
            operation_type=calculate_cd8_percent_and_cd8_density.OPERATION_TYPE.BINARY.DIVISION
        )
        calculate_cd8_percent_and_cd8_density.set_inputs(
            array_1="/slide/cd8_area_cd8_count_slide",
            array_2="/slide/tumor_plus_stroma_plus_invasive_margin_area_slide",
        )
        calculate_cd8_percent_and_cd8_density.set_outputs(
            array="/slide/cd8_percent_cd8_density_slide"
        )

        put_factors = operators.simple.general.Put(self)
        put_factors.set_params(value=[10**2, 10**6])
        put_factors.set_outputs(data="/slide/factor")

        cast_factors = operators.conversion.CastArray(self)
        cast_factors.set_params(node_type=cast_factors.NODE_TYPE.TENSOR)
        cast_factors.set_inputs(data="/slide/factor")
        cast_factors.set_outputs(array="/slide/factor_array")

        correct_units = operators.array.Math(self)
        correct_units.set_params(operation_type=correct_units.OPERATION_TYPE.BINARY.MULTIPLICATION)
        correct_units.set_inputs(
            array_1="/slide/cd8_percent_cd8_density_slide", array_2="/slide/factor_array"
        )
        correct_units.set_outputs(array="/slide/cd8_percent_cd8_density_slide")

        return correct_units

    @staticmethod
    def __set_parameters_tumor_plus_stroma(self, attachment=None):
        """
        Block of operators that set parameters for tumor+stroma statistics calculation.

        :arg attachment: Variable used for branching, or merging after branching.

        :return: Variable used for merging after branching.
        """

        set_tumor_plus_stroma_slide_statistics_names = operators.simple.general.Put(
            self, attachment=attachment
        )
        set_tumor_plus_stroma_slide_statistics_names.set_params(
            value=[
                "Tumor + Stroma: area (μm^2)",
                "Tumor + Stroma: CD8 area (μm^2)",
                "Tumor + Stroma: CD8 count",
            ]
        )
        set_tumor_plus_stroma_slide_statistics_names.set_outputs(
            data="/statistics_per_slide_names_area_cd8_area_cd8_count"
        )

        set_tumor_plus_stroma_slide_statistics_names = operators.simple.general.Put(self)
        set_tumor_plus_stroma_slide_statistics_names.set_params(
            value=["Tumor + Stroma: CD8 % area (%)", "Tumor + Stroma: CD8 density (nuclei/mm^2)"]
        )
        set_tumor_plus_stroma_slide_statistics_names.set_outputs(
            data="/statistics_per_slide_names_cd8_percent_cd8_density"
        )

        return set_tumor_plus_stroma_slide_statistics_names

    @staticmethod
    def __set_parameters_tumor_plus_stroma_plus_invasive_margin(self, attachment=None):
        """
        Block of operators that set parameters for tumor+stroma+invasive margin statistics
        calculation.

        :arg attachment: Variable used for branching, or merging after branching.

        :return: Variable used for merging after branching.
        """

        set_tumor_plus_stroma_plus_invasive_margin_slide_statistics_names = (
            operators.simple.general.Put(self, attachment=attachment)
        )
        set_tumor_plus_stroma_plus_invasive_margin_slide_statistics_names.set_params(
            value=[
                "Tumor + Stroma + Invasive Margin: area (μm^2)",
                "Tumor + Stroma + Invasive Margin: CD8 area (μm^2)",
                "Tumor + Stroma + Invasive Margin: CD8 count",
            ]
        )
        set_tumor_plus_stroma_plus_invasive_margin_slide_statistics_names.set_outputs(
            data="/statistics_per_slide_names_area_cd8_area_cd8_count"
        )

        set_tumor_plus_stroma_plus_invasive_margin_slide_statistics_names = (
            operators.simple.general.Put(self)
        )
        set_tumor_plus_stroma_plus_invasive_margin_slide_statistics_names.set_params(
            value=[
                "Tumor + Stroma + Invasive Margin: CD8 % area (%)",
                "Tumor + Stroma + Invasive Margin: CD8 density (nuclei/mm^2)",
            ]
        )
        set_tumor_plus_stroma_plus_invasive_margin_slide_statistics_names.set_outputs(
            data="/statistics_per_slide_names_cd8_percent_cd8_density"
        )

        return set_tumor_plus_stroma_plus_invasive_margin_slide_statistics_names

    @staticmethod
    def __upload_tumor_plus_stroma_statistics(self, attachment=None):
        """
        Block of operators that upload statistics per tumor+stroma.

        :arg attachment: Variable used for branching, or merging after branching.

        :return: Variable used for merging after branching.
        """

        upload_tumor_plus_stroma_statistics_per_slide = operators.image_dx.properties.Upload(
            self, attachment=attachment
        )
        upload_tumor_plus_stroma_statistics_per_slide.set_inputs(
            properties="/slide/tumor_plus_stroma_area_cd8_area_cd8_count_slide"
        )
        upload_tumor_plus_stroma_statistics_per_slide.set_params(
            type=upload_tumor_plus_stroma_statistics_per_slide.TYPE.IMAGE,
            override=True,
        )
        upload_tumor_plus_stroma_statistics_per_slide.set_params_reference(
            names="/statistics_per_slide_names_area_cd8_area_cd8_count"
        )
        upload_tumor_plus_stroma_statistics_per_slide.set_params_promotion(ids="image_id")

        upload_tumor_plus_stroma_statistics_per_slide = operators.image_dx.properties.Upload(self)
        upload_tumor_plus_stroma_statistics_per_slide.set_inputs(
            properties="/slide/cd8_percent_cd8_density_slide"
        )
        upload_tumor_plus_stroma_statistics_per_slide.set_params(
            type=upload_tumor_plus_stroma_statistics_per_slide.TYPE.IMAGE,
            override=True,
        )
        upload_tumor_plus_stroma_statistics_per_slide.set_params_reference(
            names="/statistics_per_slide_names_cd8_percent_cd8_density"
        )
        upload_tumor_plus_stroma_statistics_per_slide.set_params_promotion(ids="image_id")

        return upload_tumor_plus_stroma_statistics_per_slide

    @staticmethod
    def __upload_tumor_plus_stroma_plus_invasive_margin_statistics(self, attachment=None):
        """
        Block of operators that upload statistics per tumor+stroma+invasive margin.

        :arg attachment: Variable used for branching, or merging after branching.

        :return: Variable used for merging after branching.
        """

        upload_tumor_plus_stroma_plus_invasive_margin_statistics_per_slide = (
            operators.image_dx.properties.Upload(self, attachment=attachment)
        )
        upload_tumor_plus_stroma_plus_invasive_margin_statistics_per_slide.set_inputs(
            properties="/slide/tumor_plus_stroma_plus_invasive_margin_area_cd8_area_cd8_count_slide"
        )
        upload_tumor_plus_stroma_plus_invasive_margin_statistics_per_slide.set_params(
            type=upload_tumor_plus_stroma_plus_invasive_margin_statistics_per_slide.TYPE.IMAGE,
            override=True,
        )
        upload_tumor_plus_stroma_plus_invasive_margin_statistics_per_slide.set_params_reference(
            names="/statistics_per_slide_names_area_cd8_area_cd8_count"
        )
        upload_tumor_plus_stroma_plus_invasive_margin_statistics_per_slide.set_params_promotion(
            ids="image_id"
        )

        upload_tumor_plus_stroma_plus_invasive_margin_statistics_per_slide = (
            operators.image_dx.properties.Upload(self)
        )
        upload_tumor_plus_stroma_plus_invasive_margin_statistics_per_slide.set_inputs(
            properties="/slide/cd8_percent_cd8_density_slide"
        )
        upload_tumor_plus_stroma_plus_invasive_margin_statistics_per_slide.set_params(
            type=upload_tumor_plus_stroma_plus_invasive_margin_statistics_per_slide.TYPE.IMAGE,
            override=True,
        )
        upload_tumor_plus_stroma_plus_invasive_margin_statistics_per_slide.set_params_reference(
            names="/statistics_per_slide_names_cd8_percent_cd8_density"
        )
        upload_tumor_plus_stroma_plus_invasive_margin_statistics_per_slide.set_params_promotion(
            ids="image_id"
        )

        return upload_tumor_plus_stroma_plus_invasive_margin_statistics_per_slide

    @staticmethod
    def __classify_slide(self, attachment=None):
        """
        Block of operators that determine whether a slide is inflamed, deserted, or excluded.

        :arg attachment: Variable used for branching, or merging after branching.

        :return: Variable used for merging after branching.
        """

        compare_tumor_area = operators.simple.numeric.Compare(self, attachment=attachment)
        compare_tumor_area.set_params(
            compare_type=compare_tumor_area.COMPARE_TYPE.NOT_EQUAL, value=0.0
        )
        compare_tumor_area.set_inputs(datum="/slide/tumor_area_simple_slide")
        compare_tumor_area.set_outputs(result="/tumor_flag")

        compare_stroma_area = operators.simple.numeric.Compare(self)
        compare_stroma_area.set_params(
            compare_type=compare_stroma_area.COMPARE_TYPE.NOT_EQUAL, value=0.0
        )
        compare_stroma_area.set_inputs(datum="/slide/stroma_area_simple_slide")
        compare_stroma_area.set_outputs(result="/stroma_flag")

        tumor_and_stroma = operators.simple.numeric.Boolean(self)
        tumor_and_stroma.set_params(operation_type=tumor_and_stroma.OPERATION_TYPE.BINARY.AND)
        tumor_and_stroma.set_inputs(node_1="/tumor_flag", node_2="/stroma_flag")
        tumor_and_stroma.set_outputs(result="/tumor_and_stroma_flag")

        convert_to_bool = operators.conversion.ConvertPrimitive(self)
        convert_to_bool.set_params(output_type=convert_to_bool.OUTPUT_TYPE.BOOLEAN)
        convert_to_bool.set_inputs(node="/tumor_and_stroma_flag")
        convert_to_bool.set_outputs(node="/tumor_and_stroma_flag")

        if_else_tumor_and_stroma = operators.branching.IfElse(self)
        if_else_tumor_and_stroma.set_inputs(flag="/tumor_and_stroma_flag")

        compare_tumor_cd8_percent = operators.simple.numeric.Compare(
            self, (if_else_tumor_and_stroma, True)
        )
        compare_tumor_cd8_percent.set_params(
            compare_type=compare_tumor_cd8_percent.COMPARE_TYPE.GREATER_THAN, value=1.3
        )
        compare_tumor_cd8_percent.set_inputs(datum="/slide/tumor_cd8_percent_slide")
        compare_tumor_cd8_percent.set_outputs(result="/tumor_cd8_percent_flag")

        if_else_tumor_cd8_percent = operators.branching.IfElse(self)
        if_else_tumor_cd8_percent.set_inputs(flag="/tumor_cd8_percent_flag")

        set_slide_class_inflamed = operators.simple.general.Put(
            self, (if_else_tumor_cd8_percent, True)
        )
        set_slide_class_inflamed.set_params(value=["Inflamed"])
        set_slide_class_inflamed.set_outputs(data="/slide/slide_class")

        extract_tumor_stroma_ratio = operators.array.Manipulation(
            self, (if_else_tumor_cd8_percent, False)
        )
        extract_tumor_stroma_ratio.set_params(
            array_operation_type=extract_tumor_stroma_ratio.ARRAY_OPERATION_TYPE.EXTRACT,
            index=0,
            axis=0,
        )
        extract_tumor_stroma_ratio.set_inputs(array="/slide/tumor_stroma_ratio")
        extract_tumor_stroma_ratio.set_outputs(result="/slide/tumor_stroma_ratio")

        compare_tumor_stroma_ratio = operators.simple.numeric.Compare(self)
        compare_tumor_stroma_ratio.set_params(
            compare_type=compare_tumor_stroma_ratio.COMPARE_TYPE.GREATER_THAN, value=0.25
        )
        compare_tumor_stroma_ratio.set_inputs(datum="/slide/tumor_stroma_ratio")
        compare_tumor_stroma_ratio.set_outputs(result="/tumor_stroma_ratio_flag")

        if_else_tumor_stroma_ratio = operators.branching.IfElse(self)
        if_else_tumor_stroma_ratio.set_inputs(flag="/tumor_stroma_ratio_flag")

        set_slide_class_desert = operators.simple.general.Put(
            self, (if_else_tumor_stroma_ratio, True)
        )
        set_slide_class_desert.set_params(value=["Desert"])
        set_slide_class_desert.set_outputs(data="/slide/slide_class")

        set_slide_class_excluded = operators.simple.general.Put(
            self, (if_else_tumor_stroma_ratio, False)
        )
        set_slide_class_excluded.set_params(value=["Excluded"])
        set_slide_class_excluded.set_outputs(data="/slide/slide_class")

        join_tumor_stroma_ratio = operators.branching.Join(
            self, [set_slide_class_desert, set_slide_class_excluded]
        )

        join_tumor_cd8_percent = operators.branching.Join(
            self, [set_slide_class_inflamed, join_tumor_stroma_ratio]
        )

        upload_slide_class = RegularStatistics.__upload_slide_class(self, join_tumor_cd8_percent)

        join_tumor_and_stroma = operators.branching.Join(
            self, [upload_slide_class, if_else_tumor_and_stroma]
        )

        return join_tumor_and_stroma

    @staticmethod
    def __upload_slide_class(self, attachment=None):
        """
        Block of operators that upload slide class as a property.

        :arg attachment: Variable used for merging after branching.

        :return: Variable used for merging after branching.
        """

        upload_slide_class = operators.image_dx.properties.Upload(self, attachment=attachment)
        upload_slide_class.set_inputs(properties="/slide/slide_class")
        upload_slide_class.set_params(
            type=upload_slide_class.TYPE.IMAGE,
            names=["Inflammation Status"],
            override=True,
        )
        upload_slide_class.set_params_promotion(ids="image_id")

        return upload_slide_class

    @staticmethod
    def __upload_statistics_per_tissue(self, attachment=None):
        """
        Block of operators that upload statistics per tissue.

        :arg attachment: Variable used for branching, or merging after branching.

        :return: Variable used for merging after branching.
        """

        upload_statistics_per_tissue = operators.image_dx.properties.Upload(
            self, attachment=attachment
        )
        upload_statistics_per_tissue.set_inputs(properties="/slide/region_area_array")
        upload_statistics_per_tissue.set_params(
            type=upload_statistics_per_tissue.TYPE.IMAGE,
            names=["Tissue: area (μm^2)"],
            override=True,
        )
        upload_statistics_per_tissue.set_params_promotion(ids="image_id")

        return upload_statistics_per_tissue
