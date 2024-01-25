from pipeline_processor.core.data.constant import Constant
from pipeline_processor.operators.conversion.convert_primitive import OutputType
from py_pipeline import operators, sub_pipes
from py_pipeline.core import Pipe, special_params
from py_pipeline.data import Path
from py_pipeline.data import QP_HDAB
from typing import List, Union
from pipeline_processor.core.utils import AggregationMode
from pipeline_processor.operators.io.csv.write import Mode as CsvMode
from pipeline_processor.utils.type_utils import Number

STARDIST_MODEL_CONFIG = Path("/Users/revealbio/Datasets/LF CD8 Nuc Seg Data Augmentation/LF_CD8_Augmented_Model_Files/config.yaml")
STARDIST_MODEL_PATH = Path("/Users/revealbio/Datasets/LF CD8 Nuc Seg Data Augmentation/LF_CD8_Augmented_Model_Files/epoch 49 step 25100.ckpt")
REGION_TERMS = ["Parent"]
NUCLEUS_TERM = "nucleus"
CLASS_TERMS_TO_CLASS_IDS = {
    "nucleus": 1,
    "positive": 2,
}
TRAINING_CLASS_TERMS = list(CLASS_TERMS_TO_CLASS_IDS.keys())
DECOMPOSE_BASIS_VECTORS = QP_HDAB

class NuclearSegmentationThreshold(Pipe):
    """
    Author: Dragana Stojnev <dstojnev@revealbio.com>
    Author: Stacy Littlechild <slittlechild@revealbio.com>
    Author: Uros Milivojevic <uros@revealbio.com>
    Author: Pranav Chhibber <pranav@revealbio.com>
    Author: Jason Roberts <jroberts@revealbio.com>
    Version: 1.0.0

    Performs nuclear segmentation over given slide using the StarDist model.
    Nuclei are filtered and a RandomForest classifier is applied to upload
    only CD8 positive cells to imageDx.

    :var slide_path: Path to the WSI file.
    :var project_id: ID of a study on imageDx.
    :var image_id: ID of an image from the imageDx study specified by the `project_id`.
    :var stardist_model_path: Path to the StarDist model.
    :var stardist_model_config: Path to StarDist config file.
    """

    def __init__(self):
        super().__init__()

        # Special parameters.
        self.__slide_path = self._add_param(**special_params.slide_path)
        self.__project_id = self._add_param(**special_params.project_id)
        self.__image_id = self._add_param(**special_params.image_id)
        
        self.__decompose_basis_vectors = self._add_param(
            "decompose_basis_vectors", List[List[Number]], value=DECOMPOSE_BASIS_VECTORS
        )

        self.__stardist_model_path = self._add_param(
            "stardist_model_path", Path, required=True, value=STARDIST_MODEL_PATH
        )
        self.__stardist_model_config = self._add_param(
            "stardist_model_config", Path, required=True, value=STARDIST_MODEL_CONFIG
        )
        #self.__csv_mode = self._add_param("csv_mode", CsvMode, value=CsvMode.APPEND)
        #self.__features_path = self._add_param("features_path", Path, FEATURES_PATH)
        

    def create_pipeline(self):
        """
        Loads the slide, clears previous data, preforms nuclear segmentation via stardist, filters for positive DAB cells, calcuates stats, and uploads to ImageDx.
        """

        load_slide = operators.wsi.LoadSlide(self)
        load_slide.set_params_promotion(
            slide_path="slide_path", project_id="project_id", image_id="image_id"
        )
        load_slide.set_outputs(slide="/slide")
        NuclearSegmentationThreshold.clear_data(self)
        NuclearSegmentationThreshold.prepare_data(self)
        NuclearSegmentationThreshold.iterate(self)
        NuclearSegmentationThreshold.segment(self)
        NuclearSegmentationThreshold.filter(self)
     
        NuclearSegmentationThreshold.aggregate(self)
        NuclearSegmentationThreshold.upload(self)

        NuclearSegmentationThreshold.image_stats(self)
        


    @staticmethod
    def prepare_data(self, attachment=None):
        """TODO"""
        #Get micron per pixel value avg
        microns = operators.general.ExtractProperty(self, attachment=None)
        microns.set_params(property_names=microns.PROPERTY_NAMES.SLIDE.MPP_AVG)
        microns.set_inputs(node="/slide")
        microns.set_outputs(attributes="/slide/mpp")
        
        # data_printer= operators.debug.DataPrinter(self)
        # data_printer.set_inputs(args="/slide/mpp")
        
        #Find Inverse of avg mpp
        calculate_optimal_downsample = operators.simple.numeric.Math(self)
        calculate_optimal_downsample.set_inputs(datum_1="/slide/mpp")
        calculate_optimal_downsample.set_params(
            operation_type=calculate_optimal_downsample.OPERATION_TYPE.UNARY.MULTIPLICATIVE_INVERSE
        )
        calculate_optimal_downsample.set_outputs(result="/slide/optimal_downsample")
        #operators.macro.DataPrinter(self, args="/slide/optimal_downsample")
        
        #Round up to nearest whole number and convert to integer
        calculate_optimal_downsample = operators.simple.numeric.Math(self)
        calculate_optimal_downsample.set_inputs(datum_1="/slide/optimal_downsample")
        calculate_optimal_downsample.set_params(
            operation_type=calculate_optimal_downsample.OPERATION_TYPE.UNARY.CEIL
        )
        calculate_optimal_downsample.set_outputs(result="/slide/optimal_downsample")
        #operators.macro.DataPrinter(self, args="/slide/optimal_downsample")
        
        convert_mpp_to_int = operators.conversion.ConvertPrimitive(self)
        convert_mpp_to_int.set_inputs(node="/slide/optimal_downsample")
        convert_mpp_to_int.set_params(output_type=convert_mpp_to_int.OUTPUT_TYPE.INTEGER)
        convert_mpp_to_int.set_outputs(node="/slide/optimal_downsample")
        
        #Get micron per pixel area
        micron_area = operators.simple.numeric.Math(self)
        micron_area.set_inputs(datum_1="/slide/mpp", datum_2=Constant(2))
        micron_area.set_params(operation_type=micron_area.OPERATION_TYPE.BINARY.POWER)
        micron_area.set_outputs(result="/slide/mpp/area")
       
       #Read slide region with optimal downsample
        read_region = operators.wsi.ReadRegion(self)
        read_region.set_inputs(slide="/slide")
        read_region.set_params(x=0, y=0)
        read_region.set_params_reference(zoom="/slide/optimal_downsample")
        read_region.set_outputs(tile="/slide/ws_tile")

        load_annotations = operators.image_dx.annotations.Load(self)
        load_annotations.set_params_promotion(
            project_id="project_id",
            image_id="image_id",
        )
        load_annotations.set_params(
            annotation_type=load_annotations.ANNOTATION_TYPE.USER,
            terms=REGION_TERMS
        )
        load_annotations.set_inputs(slide="/slide")
        load_annotations.set_outputs(
            mask="/slide/ws_tile/annotation", properties="/slide/ws_tile/annotation_properties"
        )
        calc_cell_area = operators.general.ExtractProperty(self)
        calc_cell_area.set_inputs(node="/slide/ws_tile/annotation")
        calc_cell_area.set_params(
             property_names=calc_cell_area.PROPERTY_NAMES.MASK.AREA
         )
        calc_cell_area.set_outputs(attributes="/slide/cell_area")
        #operators.macro.DataPrinter(self, args="/slide/cell_area")
        
        
        shift = operators.mask.transformation.Rescale(self)
        shift.set_params(rescale_direction=shift.RESCALE_DIRECTION.SLIDE_TO_TILE)
        shift.set_inputs(mask="/slide/ws_tile/annotation")
        shift.set_outputs(mask="/slide/ws_tile/annotation")
        
        calc_cell_area = operators.general.ExtractProperty(self)
        calc_cell_area.set_inputs(node="/slide/ws_tile/annotation")
        calc_cell_area.set_params(
             property_names=calc_cell_area.PROPERTY_NAMES.MASK.AREA
         )
        calc_cell_area.set_outputs(attributes="/slide/cell_area")
        #operators.macro.DataPrinter(self, args="/slide/cell_area")
        
        
        #Find annotation areas and IDs
        area = operators.features.generation.Shape(self)
        area.set_inputs(mask="/slide/ws_tile/annotation")
        area.set_params(feature=area.FEATURE.AREA)
        area.set_params_reference(mpp="/slide/mpp")
        area.set_outputs(features="/slide/target")
        
        # data_printer = operators.debug.DataPrinter(self)
        # data_printer.set_inputs(args="/slide/target")
        
        #iteratate over each annotation ID 
        property_iterator = operators.array.Iterator(self)
        property_iterator.set_inputs(array="/slide/target")
        property_iterator.set_params(axis=0)
        property_iterator.set_outputs(element="/slide/target_element")
        
        # data_printer = operators.debug.DataPrinter(self)
        # data_printer.set_inputs(args="/slide/target_element")
        
        #extract annotation ID
        extract_id = operators.array.Manipulation(self)
        extract_id.set_inputs(array="/slide/target_element")
        extract_id.set_params(
            array_operation_type=extract_id.ARRAY_OPERATION_TYPE.EXTRACT, index=0, axis=0
        )
        extract_id.set_outputs(result="/slide/target/id")
        
        #extract annotation area
        extract_area = operators.array.Manipulation(self)
        extract_area.set_inputs(array="/slide/target_element")
        extract_area.set_params(
            array_operation_type=extract_area.ARRAY_OPERATION_TYPE.EXTRACT, index=1, axis=0
        )
        extract_area.set_outputs(result="/slide/features_area")
        
        #convert annotation ID to interger
        convert_id_to_int = operators.conversion.ConvertPrimitive(self)
        convert_id_to_int.set_inputs(node="/slide/target/id")
        convert_id_to_int.set_params(output_type=convert_id_to_int.OUTPUT_TYPE.INTEGER)
        convert_id_to_int.set_outputs(node="/slide/target/id")
        
        #filter annotations masks and extract current block for downstream processing
        roi = operators.mask.filtering.Labels(self)
        roi.set_params(operation_type=roi.OPERATION_TYPE.INCLUDE)
        roi.set_params_reference(labels="/slide/target/id")
        roi.set_inputs(mask="/slide/ws_tile/annotation")
        roi.set_outputs(mask="/slide/ws_tile/annotation/block")
        
        #operators.macro.ShowImage(self, images="/slide/ws_tile/annotation/block")

    @staticmethod
    def iterate(self):
        """
        Iterates slide over annotation mask, calls stardist on each tile.
        """
        #plot_mask = operators.debug.ShowImage(self)
        #plot_mask.set_inputs(images="/slide/ws_tile/annotation")
        read_region_iterator = operators.wsi.ReadRegionIterator(self)
        read_region_iterator.set_params(
            size=1024,
            stride=1024 - 80,
            zoom=1,
            zoom_type=read_region_iterator.ZOOM_TYPE.DOWNSAMPLE,
            threshold=0.01,
        )
        read_region_iterator.set_inputs(slide="/slide", mask="/slide/ws_tile/annotation/block")
        read_region_iterator.set_outputs(
            tile="/slide/rgb_region", intersection_mask="/slide/region_mask"
        )
        # plot_mask = operators.debug.ShowImage(self)
        # plot_mask.set_inputs(images=("/slide/ws_tile/annotation","/slide/rgb_region", "/slide/region_mask"))
        

    @staticmethod
    def segment(self):
        """
        StarDist inference on RGB channel image. Multiplication step masks out nuclear predictions
        outside of imageDx annotation mask boundaries.
        """

        nuclear_segmentation = sub_pipes.nuclear_segmentation.NuclearSegmentationStarDist(self)
        nuclear_segmentation.set_params_promotion(
            model_config="stardist_model_config",
            model_path="stardist_model_path",
        )
        nuclear_segmentation.set_params(
            ray_length_average_minimum=4,
            ray_length_minimum=3,
        )
        nuclear_segmentation.set_inputs(input_image="/slide/rgb_region")
        nuclear_segmentation.set_outputs(output_mask="/slide/rgb_region/stardist_mask")

        intersect = operators.mask.filtering.Intersection(self)
        intersect.set_inputs(
            mask="/slide/rgb_region/stardist_mask", filter_region="/slide/region_mask"
        )
        intersect.set_params(
            threshold_type=intersect.THRESHOLD_TYPE.AREA, threshold=0, crop=False
        )
        intersect.set_outputs(filtered="/slide/rgb_region/stardist_region_mask")
        
    @staticmethod
    def filter(self):
        """TODO."""
        #Add branching operator to skip regions without stardist masks
        isempty = operators.general.ExtractProperty(self)
        isempty.set_inputs(node="/slide/rgb_region/stardist_region_mask")
        isempty.set_params(property_names=isempty.PROPERTY_NAMES.MASK.IS_EMPTY)
        isempty.set_outputs(attributes="/slide/rgb_region/stardist_region_mask/is_empty")

        ifelse = operators.branching.IfElse(self)
        ifelse.set_inputs(flag="/slide/rgb_region/stardist_region_mask/is_empty")
        
        #Decompose Image and Extract Dab Channel to data container 
        decompose = operators.image.general.Decompose(self,(ifelse,False))
        decompose.set_params(
            transpose_basis_vectors=False,
        )
        decompose.set_params_promotion(basis_vectors="decompose_basis_vectors")
        decompose.set_inputs(image="/slide/rgb_region")
        decompose.set_outputs(image="/slide/rgb_region/alpha")
        
        extract_alpha_channels = operators.array.Manipulation(self)
        extract_alpha_channels.set_params(
            array_operation_type=extract_alpha_channels.ARRAY_OPERATION_TYPE.EXTRACT,
            index=1,
            axis=2,
        )
        
        extract_alpha_channels.set_inputs(array="/slide/rgb_region/alpha")
        extract_alpha_channels.set_outputs(result="/slide/rgb_region/alpha0")
        
        # show_image = operators.debug.ShowImage(self)
        # show_image.set_inputs(images=("/slide/rgb_region/stardist_region_mask","/slide/rgb_region/alpha0"))
        # show_image.set_params(viewer=show_image.VIEWER.MATPLOTLIB)
        
        #Calculate Features of Dab channel using stardist masks
        features = operators.features.generation.Intensity(self)
        features.set_inputs(mask="/slide/rgb_region/stardist_region_mask", image="/slide/rgb_region/alpha0")
        features.set_params(feature=[features.FEATURE.PERCENTILE_99])
        features.set_outputs(features="/slide/rgb_region/features")
        
        # data_printer = operators.debug.DataPrinter(self)
        # data_printer.set_inputs(args="/slide/rgb_region/features")
        
        #Filter for positive Dab cells by excluding objects below threshold value
        filter_by_intensity = operators.array.Filter(self)
        filter_by_intensity.set_inputs(array="/slide/rgb_region/features")
        filter_by_intensity.set_params(
            index=1,
            axis=1,
             operation_type=filter_by_intensity.OPERATION_TYPE.EXCLUDE,
             compare_type=filter_by_intensity.COMPARE_TYPE.LESS_THAN,
            threshold=1,
         )
        filter_by_intensity.set_outputs(array="/slide/rgb_region/filtered_features")
        
        #Filter for Negative Dab Cells by including objects below threshold value
        filter_by_intensity = operators.array.Filter(self)
        filter_by_intensity.set_inputs(array="/slide/rgb_region/features")
        filter_by_intensity.set_params(
            index=1,
            axis=1,
             operation_type=filter_by_intensity.OPERATION_TYPE.INCLUDE,
             compare_type=filter_by_intensity.COMPARE_TYPE.LESS_THAN,
            threshold=1,
         )
        filter_by_intensity.set_outputs(array="/slide/rgb_region/filtered_features_neg")
        
        #data_printer = operators.debug.DataPrinter(self)
        #data_printer.set_inputs(args="/slide/rgb_region/filtered_features")
        
        #Extract the labels of the positive filtered data set
        extract_labels = operators.array.Manipulation(self)
        extract_labels.set_params(
        index=0,
        axis=1,
        array_operation_type=extract_labels.ARRAY_OPERATION_TYPE.EXTRACT,
    )
        extract_labels.set_inputs(array="/slide/rgb_region/filtered_features")
        extract_labels.set_outputs(result="/labels")
        
        #Filter the stardist mask to include only extracted labels
        filter_cells_pos = operators.mask.filtering.Labels(self)
        filter_cells_pos.set_inputs(mask="/slide/rgb_region/stardist_region_mask")
        filter_cells_pos.set_params(operation_type=filter_cells_pos.OPERATION_TYPE.INCLUDE)
        filter_cells_pos.set_params_reference(labels="/labels")
        filter_cells_pos.set_outputs(mask="/slide/rgb_region/stardist_region_mask_pos")
        
        #Extract the labels of the negative filtered data set
        extract_labels = operators.array.Manipulation(self)
        extract_labels.set_params(
        index=0,
        axis=1,
        array_operation_type=extract_labels.ARRAY_OPERATION_TYPE.EXTRACT,
    )
        extract_labels.set_inputs(array="/slide/rgb_region/filtered_features_neg")
        extract_labels.set_outputs(result="/labels_neg")
        
        #Filter the stardist mask to include only negative extracted labels
        filter_cells_neg = operators.mask.filtering.Labels(self)
        filter_cells_neg.set_inputs(mask="/slide/rgb_region/stardist_region_mask")
        filter_cells_neg.set_params(operation_type=filter_cells_pos.OPERATION_TYPE.INCLUDE)
        filter_cells_neg.set_params_reference(labels="/labels_neg")
        filter_cells_neg.set_outputs(mask="/slide/rgb_region/stardist_region_mask_neg")
        
        duplicate = operators.general.DuplicateNode(self,attachment=(ifelse,True))
        duplicate.set_inputs(node="/slide/rgb_region/stardist_region_mask")
        duplicate.set_outputs(duplicate = "/slide/rgb_region/stardist_region_mask_pos")
        
        duplicate = operators.general.DuplicateNode(self)
        duplicate.set_inputs(node="/slide/rgb_region/stardist_region_mask")
        duplicate.set_outputs(duplicate = "/slide/rgb_region/stardist_region_mask_neg")
        
        operators.branching.Join(self,[duplicate, filter_cells_neg])
        
    @staticmethod
    def aggregate(self):
        """TODO."""
        #Aggregate and passthrough annotation
        ann_agg = operators.mask.general.Aggregator(self)
        ann_agg.set_params(merge=False, rescale=True)
        ann_agg.set_inputs(mask="/slide/region_mask")
        ann_agg.set_outputs(mask="/slide/aggregated_region_mask")
        ann_agg.set_mode(mode=AggregationMode.PASSTHROUGH)
        
        # Aggregate and passthrough stardist mask
        nucleus_agg = operators.mask.general.Aggregator(self)
        nucleus_agg.set_params(merge=False, rescale=True)
        nucleus_agg.set_inputs(mask="/slide/rgb_region/stardist_region_mask")
        nucleus_agg.set_outputs(mask="/slide/aggregated_stardist_mask")
        nucleus_agg.set_mode(mode=AggregationMode.PASSTHROUGH)

        # Aggregate and passthrough stardist mask of positive cells
        nucleus_pos_agg = operators.mask.general.Aggregator(self)
        nucleus_pos_agg.set_params(merge=False, rescale=True)
        nucleus_pos_agg.set_inputs(mask="/slide/rgb_region/stardist_region_mask_pos")
        nucleus_pos_agg.set_outputs(mask="/slide/aggregated_stardist_mask_pos")
        nucleus_pos_agg.set_mode(mode=AggregationMode.PASSTHROUGH)
       
        #Aggregate and close stardist mask of negative cells
        nucleus_neg_agg = operators.mask.general.Aggregator(self)
        nucleus_neg_agg.set_params(merge=False, rescale=True)
        nucleus_neg_agg.set_inputs(mask="/slide/rgb_region/stardist_region_mask_neg")
        nucleus_neg_agg.set_outputs(mask="/slide/aggregated_stardist_mask_neg")
        
        #masking postprocessing
        nms = operators.deep_learning.postprocessing.NonMaximumSuppression(self)
        nms.set_inputs(mask="/slide/aggregated_region_mask")
        nms.set_params(iou_threshold=0.40, metric=nms.METRIC.INTERSECTION_OVER_SMALLER_AREA)
        nms.set_outputs(mask="/slide/aggregated_region_mask")
        
        nms = operators.deep_learning.postprocessing.NonMaximumSuppression(self)
        nms.set_inputs(mask="/slide/aggregated_stardist_mask")
        nms.set_params(iou_threshold=0.40, metric=nms.METRIC.INTERSECTION_OVER_SMALLER_AREA)
        nms.set_outputs(mask="/slide/aggregated_stardist_mask")
        

        nms = operators.deep_learning.postprocessing.NonMaximumSuppression(self)
        nms.set_inputs(mask="/slide/aggregated_stardist_mask_pos")
        nms.set_params(iou_threshold=0.40, metric=nms.METRIC.INTERSECTION_OVER_SMALLER_AREA)
        nms.set_outputs(mask="/slide/aggregated_stardist_mask_pos")
        
        
        nms = operators.deep_learning.postprocessing.NonMaximumSuppression(self)
        nms.set_inputs(mask="/slide/aggregated_stardist_mask_neg")
        nms.set_params(iou_threshold=0.40, metric=nms.METRIC.INTERSECTION_OVER_SMALLER_AREA)
        nms.set_outputs(mask="/slide/aggregated_stardist_mask_neg")
        
        NuclearSegmentationThreshold.statsperblock(self)
        
        
    @staticmethod
    def upload(self):
        #Upload positive masks with Positive term
        uploader = operators.image_dx.annotations.Upload(self)
        uploader.set_params(terms='positive')
        uploader.set_inputs(mask="/slide/aggregated_stardist_mask_pos", slide="/slide")
        #Upload Negative mask with Nucleus term
        uploader = operators.image_dx.annotations.Upload(self)
        uploader.set_params(terms=NUCLEUS_TERM)
        uploader.set_inputs(mask="/slide/aggregated_stardist_mask_neg", slide="/slide")
        
                # #Closes annotation iterator
        nucleus_neg_agg = operators.mask.general.Aggregator(self)
        nucleus_neg_agg.set_params(merge=False, rescale=True)
        nucleus_neg_agg.set_inputs(mask="/slide/ws_tile/annotation/block")
        nucleus_neg_agg.set_outputs(mask="/slide/ws_tile/annotation/agg_block")
        
    @staticmethod
    def clear_data(self):
        """TODO."""
        # Delete Nuclus and Positive Terms
        delete = operators.image_dx.annotations.Delete(self)
        delete.set_inputs(slide="/slide")
        delete.set_params(terms=[NUCLEUS_TERM,'positive'])

    @staticmethod
    def statsperblock(self):
        #Extract positive cell counts
        extract_pos_annotation_count = operators.general.ExtractProperty(self)
        extract_pos_annotation_count.set_params(
            property_names=extract_pos_annotation_count.PROPERTY_NAMES.MASK.COUNT
        )
        extract_pos_annotation_count.set_inputs(node="/slide/aggregated_stardist_mask_pos")
        extract_pos_annotation_count.set_outputs(attributes="/slide/annotation_pos_count")
        #Extract Negative cell counts
        extract_neg_annotation_count = operators.general.ExtractProperty(self)
        extract_neg_annotation_count.set_params(
            property_names=extract_neg_annotation_count.PROPERTY_NAMES.MASK.COUNT
        )
        extract_neg_annotation_count.set_inputs(node="/slide/aggregated_stardist_mask_neg")
        extract_neg_annotation_count.set_outputs(attributes="/slide/annotation_neg_count")
        #Extract total cell counts
        extract_annotation_count = operators.general.ExtractProperty(self)
        extract_annotation_count.set_params(
            property_names=extract_annotation_count.PROPERTY_NAMES.MASK.COUNT
        )
        extract_annotation_count.set_inputs(node="/slide/aggregated_stardist_mask")
        extract_annotation_count.set_outputs(attributes="/slide/annotation_count")
        
        #Calculate % CD8 Positive
        math = operators.simple.numeric.Math(self)
        math.set_params(operation_type=math.OPERATION_TYPE.BINARY.DIVISION)
        math.set_inputs(
                datum_1="/slide/annotation_pos_count",
                datum_2="/slide/annotation_count",
        )
        math.set_outputs(result="/slide/percent_pos")
        #change to percentage
        put_factors = operators.simple.general.Put(self)
        put_factors.set_params(value=100)
        put_factors.set_outputs(data="/slide/factor")
        
        math = operators.simple.numeric.Math(self)
        math.set_params(operation_type=math.OPERATION_TYPE.BINARY.MULTIPLICATION)
        math.set_inputs(
                datum_1="/slide/percent_pos",
                datum_2="/slide/factor",
        )
        math.set_outputs(result="/slide/percent_pos")
        
        calc_cell_area = operators.general.ExtractProperty(self)
        calc_cell_area.set_inputs(node="/slide/aggregated_stardist_mask")
        calc_cell_area.set_params(
             property_names=calc_cell_area.PROPERTY_NAMES.MASK.AREA
         )
        calc_cell_area.set_outputs(attributes="/slide/cell_area")
       
        scale_cell_area = operators.simple.numeric.Math(self)
        scale_cell_area.set_inputs(datum_1="/slide/cell_area", datum_2="/slide/mpp/area")
        scale_cell_area.set_params(operation_type=scale_cell_area.OPERATION_TYPE.BINARY.MULTIPLICATION)
        scale_cell_area.set_outputs(result="/slide/cell_area")
        operators.macro.DataPrinter(self, args="/slide/cell_area")
        #operators.macro.DataPrinter(self, args="/slide/cell_area/tile")
        
        #Calculate CD8 Density count/area
        math = operators.simple.numeric.Math(self)
        math.set_params(operation_type=math.OPERATION_TYPE.BINARY.DIVISION)
        math.set_inputs(
                datum_1="/slide/cell_area",
                datum_2=Constant(1000000)
        )
        math.set_outputs(result="/slide/cell_area/mm")
        
        
        math = operators.simple.numeric.Math(self)
        math.set_params(operation_type=math.OPERATION_TYPE.BINARY.DIVISION)
        math.set_inputs(
                datum_1="/slide/annotation_pos_count",
                datum_2="/slide/cell_area/mm",
        )
        math.set_outputs(result="/slide/pos_density")
        
        # #calculate CD8 area
        extract_cd8_area_in_pixels = operators.general.ExtractProperty(self)
        extract_cd8_area_in_pixels.set_inputs(node="/slide/aggregated_stardist_mask_pos")
        extract_cd8_area_in_pixels.set_params(
             property_names=extract_cd8_area_in_pixels.PROPERTY_NAMES.MASK.AREA
         )
        extract_cd8_area_in_pixels.set_outputs(attributes="/slide/cd8_area")
        
        scale_pos_area = operators.simple.numeric.Math(self)
        scale_pos_area.set_inputs(datum_1="/slide/cd8_area", datum_2="/slide/mpp/area")
        scale_pos_area.set_params(operation_type=scale_pos_area.OPERATION_TYPE.BINARY.MULTIPLICATION)
        scale_pos_area.set_outputs(result="/slide/cd8_area")
        
         # #calculate negative cell area
        extract_cd8_area_in_pixels = operators.general.ExtractProperty(self)
        extract_cd8_area_in_pixels.set_inputs(node="/slide/aggregated_stardist_mask_neg")
        extract_cd8_area_in_pixels.set_params(
             property_names=extract_cd8_area_in_pixels.PROPERTY_NAMES.MASK.AREA
         )
        extract_cd8_area_in_pixels.set_outputs(attributes="/slide/negcell_area")
        
        scale_neg_area = operators.simple.numeric.Math(self)
        scale_neg_area.set_inputs(datum_1="/slide/negcell_area", datum_2="/slide/mpp/area")
        scale_neg_area.set_params(operation_type=scale_neg_area.OPERATION_TYPE.BINARY.MULTIPLICATION)
        scale_neg_area.set_outputs(result="/slide/negcell_area")
       
        
        #calculate Analysis area
        #Rescale annotation block to slide
        shift = operators.mask.transformation.Rescale(self)
        shift.set_params(rescale_direction=shift.RESCALE_DIRECTION.TILE_TO_SLIDE)
        shift.set_inputs(mask="/slide/ws_tile/annotation/block")
        shift.set_outputs(mask="/slide/ws_tile/annotation/block/scale")
        
        #extract annotation block area
        extract_analysis_area = operators.general.ExtractProperty(self)
        extract_analysis_area.set_inputs(node="/slide/ws_tile/annotation/block/scale")
        extract_analysis_area.set_params(property_names=extract_analysis_area.PROPERTY_NAMES.MASK.AREA)
        extract_analysis_area.set_outputs(attributes ="/slide/analysis_area")
        #operators.macro.DataPrinter(self, args="/slide/analysis_area")
        
        #scale annotation area to mpp
        scale_analysis_area = operators.simple.numeric.Math(self)
        scale_analysis_area.set_inputs(datum_1="/slide/analysis_area", datum_2="/slide/mpp/area")
        scale_analysis_area.set_params(operation_type=scale_analysis_area.OPERATION_TYPE.BINARY.MULTIPLICATION)
        scale_analysis_area.set_outputs(result="/slide/analysis_area")
        
        #Insert stats to node 
        put_empty_simple = operators.simple.general.Put(self)
        put_empty_simple.set_params(value=[])
        put_empty_simple.set_outputs(data="/slide/stats")

        insert_cd8_counts = operators.simple.iterable.Manipulation(self)
        insert_cd8_counts.set_inputs(iterable="/slide/stats")
        insert_cd8_counts.set_params_reference(value="/slide/annotation_count")
        insert_cd8_counts.set_params(operation_type=insert_cd8_counts.OPERATION_TYPE.INSERT, index=0)
        insert_cd8_counts.set_outputs(result="/slide/stats")
        
        insert_cd8_counts = operators.simple.iterable.Manipulation(self)
        insert_cd8_counts.set_inputs(iterable="/slide/stats")
        insert_cd8_counts.set_params_reference(value="/slide/annotation_pos_count")
        insert_cd8_counts.set_params(operation_type=insert_cd8_counts.OPERATION_TYPE.INSERT, index=1)
        insert_cd8_counts.set_outputs(result="/slide/stats")
        
        insert_cd8_neg_counts = operators.simple.iterable.Manipulation(self)
        insert_cd8_neg_counts.set_inputs(iterable="/slide/stats")
        insert_cd8_neg_counts.set_params_reference(value="/slide/annotation_neg_count")
        insert_cd8_neg_counts.set_params(operation_type=insert_cd8_neg_counts.OPERATION_TYPE.INSERT, index=2)
        insert_cd8_neg_counts.set_outputs(result="/slide/stats")
        
        insert_cd8_percent = operators.simple.iterable.Manipulation(self)
        insert_cd8_percent.set_inputs(iterable="/slide/stats")
        insert_cd8_percent.set_params_reference(value="/slide/percent_pos")
        insert_cd8_percent.set_params(operation_type=insert_cd8_percent.OPERATION_TYPE.INSERT, index=3)
        insert_cd8_percent.set_outputs(result="/slide/stats")
        
        insert_area = operators.simple.iterable.Manipulation(self)
        insert_area.set_inputs(iterable="/slide/stats")
        insert_area.set_params_reference(value="/slide/cell_area")
        insert_area.set_params(operation_type=insert_area.OPERATION_TYPE.INSERT, index=4)
        insert_area.set_outputs(result="/slide/stats")
        
        insert_pos_density = operators.simple.iterable.Manipulation(self)
        insert_pos_density.set_inputs(iterable="/slide/stats")
        insert_pos_density.set_params_reference(value="/slide/pos_density")
        insert_pos_density.set_params(operation_type=insert_pos_density.OPERATION_TYPE.INSERT, index=5)
        insert_pos_density.set_outputs(result="/slide/stats")
        
        insert_pos_area = operators.simple.iterable.Manipulation(self)
        insert_pos_area.set_inputs(iterable="/slide/stats")
        insert_pos_area.set_params_reference(value="/slide/cd8_area")
        insert_pos_area.set_params(operation_type=insert_pos_area.OPERATION_TYPE.INSERT, index=6)
        insert_pos_area.set_outputs(result="/slide/stats")
    
        insert_neg_area = operators.simple.iterable.Manipulation(self)
        insert_neg_area.set_inputs(iterable="/slide/stats")
        insert_neg_area.set_params_reference(value="/slide/negcell_area")
        insert_neg_area.set_params(operation_type=insert_neg_area.OPERATION_TYPE.INSERT, index=7)
        insert_neg_area.set_outputs(result="/slide/stats")
        
        insert_analysis_area = operators.simple.iterable.Manipulation(self)
        insert_analysis_area.set_inputs(iterable="/slide/stats")
        insert_analysis_area.set_params_reference(value="/slide/analysis_area")
        insert_analysis_area.set_params(operation_type=insert_analysis_area.OPERATION_TYPE.INSERT, index=8)
        insert_analysis_area.set_outputs(result="/slide/stats")
    
        #cast list to array
        list = operators.conversion.CastArray(self)
        list.set_inputs(data= "/slide/stats")
        list.set_outputs(array="/slide/stats")
        list.set_params(node_type=list.NODE_TYPE.TENSOR)
        
        #data_printer2 = operators.debug.DataPrinter(self)
        #data_printer2.set_inputs (args="/slide/stats")
        # Upload calculated stats.
        upload = operators.image_dx.properties.Upload(self)
        upload.set_inputs(properties="/slide/stats")
        upload.set_params_reference(ids="/slide/target/id")
        upload.set_params(
            names=[
                   "Total Cell Count",
                   "CD8 Positive Count",
                   "CD8 Negative Count",
                   "Percent CD8 Positive",
                   "Cell area (um^2)",
                   "Positive Cell Density (count/cell area mm^2)",
                   "Positive Cell area (um^2)",
                   "Negative Cells area (um^2)",
                   "Analysis Area (um^2)"
                   ],
            type=upload.TYPE.ANNOTATION,
            override=True,
        )

        
    @staticmethod
    def image_stats(self):
        #reload annotations
        load_annotations = operators.image_dx.annotations.Load(self)
        load_annotations.set_params_promotion(
            project_id="project_id",
            image_id="image_id",
        )
        load_annotations.set_params(
            annotation_type=load_annotations.ANNOTATION_TYPE.USER,
            terms='positive',
        )
        load_annotations.set_inputs(slide="/slide")
        load_annotations.set_outputs(
            mask="/slide/whole_pos"
        )
        load_annotations = operators.image_dx.annotations.Load(self)
        load_annotations.set_params_promotion(
            project_id="project_id",
            image_id="image_id",
        )
        load_annotations.set_params(
            annotation_type=load_annotations.ANNOTATION_TYPE.USER,
            terms='nucleus',
        )
        load_annotations.set_inputs(slide="/slide")
        load_annotations.set_outputs(
            mask="/slide/whole_neg"
        )
        load_annotations = operators.image_dx.annotations.Load(self)
        load_annotations.set_params_promotion(
            project_id="project_id",
            image_id="image_id",
        )
        load_annotations.set_params(
            annotation_type=load_annotations.ANNOTATION_TYPE.USER,
            terms=[ 'positive','nucleus'],
        )
        load_annotations.set_inputs(slide="/slide")
        load_annotations.set_outputs(
            mask="/slide/whole_cell"
        )
        #Extract positive cell counts
        extract_pos_annotation_count = operators.general.ExtractProperty(self)
        extract_pos_annotation_count.set_params(
            property_names=extract_pos_annotation_count.PROPERTY_NAMES.MASK.COUNT
        )
        extract_pos_annotation_count.set_inputs(node="/slide/whole_pos")
        extract_pos_annotation_count.set_outputs(attributes="/slide/whole_pos_count")
        #Extract Negative cell counts
        extract_neg_annotation_count = operators.general.ExtractProperty(self)
        extract_neg_annotation_count.set_params(
            property_names=extract_neg_annotation_count.PROPERTY_NAMES.MASK.COUNT
        )
        extract_neg_annotation_count.set_inputs(node="/slide/whole_neg")
        extract_neg_annotation_count.set_outputs(attributes="/slide/whole_neg_count")
        
        #Extract total cell counts
        merge= operators.simple.numeric.Math(self)
        merge.set_params(operation_type=merge.OPERATION_TYPE.BINARY.ADDITION)
        merge.set_inputs(datum_1="/slide/whole_pos_count", datum_2="/slide/whole_neg_count")
        merge.set_outputs(result="/slide/whole_count")
    
        #Calculate % CD8 Positive
        math = operators.simple.numeric.Math(self)
        math.set_params(operation_type=math.OPERATION_TYPE.BINARY.DIVISION)
        math.set_inputs(
                datum_1="/slide/whole_pos_count",
                datum_2="/slide/whole_count",
        )
        math.set_outputs(result="/slide/whole_percent_pos")
        
        #change to percentage
        put_factors = operators.simple.general.Put(self)
        put_factors.set_params(value=100)
        put_factors.set_outputs(data="/slide/factor")
        
        math = operators.simple.numeric.Math(self)
        math.set_params(operation_type=math.OPERATION_TYPE.BINARY.MULTIPLICATION)
        math.set_inputs(
                datum_1="/slide/whole_percent_pos",
                datum_2="/slide/factor",
        )
        math.set_outputs(result="/slide/whole_percent_pos")
        
        #calculate cell area
        extract_cd8_area_in_pixels = operators.general.ExtractProperty(self)
        extract_cd8_area_in_pixels.set_inputs(node="/slide/whole_cell")
        extract_cd8_area_in_pixels.set_params(
            property_names=extract_cd8_area_in_pixels.PROPERTY_NAMES.MASK.AREA
        )
        extract_cd8_area_in_pixels.set_outputs(attributes="/slide/whole_cell_area")
        
        scale_cell_area = operators.simple.numeric.Math(self)
        scale_cell_area.set_inputs(datum_1="/slide/whole_cell_area", datum_2="/slide/mpp/area")
        scale_cell_area.set_params(operation_type=scale_cell_area.OPERATION_TYPE.BINARY.MULTIPLICATION)
        scale_cell_area.set_outputs(result="/slide/whole_cell_area")
        
        #Calculate CD8 Density count/area
        math = operators.simple.numeric.Math(self)
        math.set_params(operation_type=math.OPERATION_TYPE.BINARY.DIVISION)
        math.set_inputs(
                datum_1="/slide/whole_cell_area",
                datum_2=Constant(1000000)
        )
        math.set_outputs(result="/slide/whole_cell_area/mm")
        
        
        
        math = operators.simple.numeric.Math(self)
        math.set_params(operation_type=math.OPERATION_TYPE.BINARY.DIVISION)
        math.set_inputs(
                datum_1="/slide/whole_pos_count",
                datum_2="/slide/whole_cell_area/mm",
        )
        math.set_outputs(result="/slide/whole_pos_density")
        
        #calculate Pos cell area
        pos_cell_area = operators.general.ExtractProperty(self)
        pos_cell_area.set_inputs(node="/slide/whole_pos")
        pos_cell_area.set_params(
            property_names=pos_cell_area.PROPERTY_NAMES.MASK.AREA
        )
        pos_cell_area.set_outputs(attributes="/slide/whole_pos_area")
        
        scale_pos_cell_area = operators.simple.numeric.Math(self)
        scale_pos_cell_area.set_inputs(datum_1="/slide/whole_pos_area", datum_2="/slide/mpp/area")
        scale_pos_cell_area.set_params(operation_type=scale_pos_cell_area.OPERATION_TYPE.BINARY.MULTIPLICATION)
        scale_pos_cell_area.set_outputs(result="/slide/whole_pos_area")
        
        #calculate neg cell area
        neg_cell_area = operators.general.ExtractProperty(self)
        neg_cell_area.set_inputs(node="/slide/whole_neg")
        neg_cell_area.set_params(
            property_names=neg_cell_area.PROPERTY_NAMES.MASK.AREA
        )
        neg_cell_area.set_outputs(attributes="/slide/whole_neg_area")
        
        scale_pos_cell_area = operators.simple.numeric.Math(self)
        scale_pos_cell_area.set_inputs(datum_1="/slide/whole_neg_area", datum_2="/slide/mpp/area")
        scale_pos_cell_area.set_params(operation_type=scale_pos_cell_area.OPERATION_TYPE.BINARY.MULTIPLICATION)
        scale_pos_cell_area.set_outputs(result="/slide/whole_neg_area")
        
        #calculate Analysis area
        #Rescale annotation block to slide
        shift = operators.mask.transformation.Rescale(self)
        shift.set_params(rescale_direction=shift.RESCALE_DIRECTION.TILE_TO_SLIDE)
        shift.set_inputs(mask="/slide/ws_tile/annotation/")
        shift.set_outputs(mask="/slide/ws_tile/annotation/scale")
        
        #extract annotation area
        extract_analysis_area = operators.general.ExtractProperty(self)
        extract_analysis_area.set_inputs(node="/slide/ws_tile/annotation/scale")
        extract_analysis_area.set_params(property_names=extract_analysis_area.PROPERTY_NAMES.MASK.AREA)
        extract_analysis_area.set_outputs(attributes ="/slide/whole_analysis_area")
        operators.macro.DataPrinter(self, args="/slide/whole_analysis_area")
        
        #scale annotation area to mpp
        scale_analysis_area = operators.simple.numeric.Math(self)
        scale_analysis_area.set_inputs(datum_1="/slide/whole_analysis_area", datum_2="/slide/mpp/area")
        scale_analysis_area.set_params(operation_type=scale_analysis_area.OPERATION_TYPE.BINARY.MULTIPLICATION)
        scale_analysis_area.set_outputs(result="/slide/whole_analysis_area")
        operators.macro.DataPrinter(self, args="/slide/whole_analysis_area")
        
        #Insert stats to node 
        put_empty_simple = operators.simple.general.Put(self)
        put_empty_simple.set_params(value=[])
        put_empty_simple.set_outputs(data="/slide/stats_image")
        
        #Total Cell Count
        insert_cd8_neg_counts = operators.simple.iterable.Manipulation(self)
        insert_cd8_neg_counts.set_inputs(iterable="/slide/stats_image")
        insert_cd8_neg_counts.set_params_reference(value="/slide/whole_count")
        insert_cd8_neg_counts.set_params(operation_type=insert_cd8_neg_counts.OPERATION_TYPE.INSERT, index=0)
        insert_cd8_neg_counts.set_outputs(result="/slide/stats_image")
        
        #Positive Cell Count
        insert_cd8_counts = operators.simple.iterable.Manipulation(self)
        insert_cd8_counts.set_inputs(iterable="/slide/stats_image")
        insert_cd8_counts.set_params_reference(value="/slide/whole_pos_count")
        insert_cd8_counts.set_params(operation_type=insert_cd8_counts.OPERATION_TYPE.INSERT, index=1)
        insert_cd8_counts.set_outputs(result="/slide/stats_image")
        
        #Negative Cell Count
        insert_cd8_neg_counts = operators.simple.iterable.Manipulation(self)
        insert_cd8_neg_counts.set_inputs(iterable="/slide/stats_image")
        insert_cd8_neg_counts.set_params_reference(value="/slide/whole_neg_count")
        insert_cd8_neg_counts.set_params(operation_type=insert_cd8_neg_counts.OPERATION_TYPE.INSERT, index=2)
        insert_cd8_neg_counts.set_outputs(result="/slide/stats_image")
        
        #Percent Positive
        insert_cd8_percent = operators.simple.iterable.Manipulation(self)
        insert_cd8_percent.set_inputs(iterable="/slide/stats_image")
        insert_cd8_percent.set_params_reference(value="/slide/whole_percent_pos")
        insert_cd8_percent.set_params(operation_type=insert_cd8_percent.OPERATION_TYPE.INSERT, index=3)
        insert_cd8_percent.set_outputs(result="/slide/stats_image")
        
        #Cell area
        insert_area = operators.simple.iterable.Manipulation(self)
        insert_area.set_inputs(iterable="/slide/stats_image")
        insert_area.set_params_reference(value="/slide/whole_cell_area")
        insert_area.set_params(operation_type=insert_area.OPERATION_TYPE.INSERT, index=4)
        insert_area.set_outputs(result="/slide/stats_image")
        
        #Pos cell density
        insert_pos_density = operators.simple.iterable.Manipulation(self)
        insert_pos_density.set_inputs(iterable="/slide/stats_image")
        insert_pos_density.set_params_reference(value="/slide/whole_pos_density")
        insert_pos_density.set_params(operation_type=insert_pos_density.OPERATION_TYPE.INSERT, index=5)
        insert_pos_density.set_outputs(result="/slide/stats_image")
        
        #Pos cell area
        insert_pos_area = operators.simple.iterable.Manipulation(self)
        insert_pos_area.set_inputs(iterable="/slide/stats_image")
        insert_pos_area.set_params_reference(value="/slide/whole_pos_area")
        insert_pos_area.set_params(operation_type=insert_pos_area.OPERATION_TYPE.INSERT, index=6)
        insert_pos_area.set_outputs(result="/slide/stats_image")
    
        #neg cell area
        insert_neg_area = operators.simple.iterable.Manipulation(self)
        insert_neg_area.set_inputs(iterable="/slide/stats_image")
        insert_neg_area.set_params_reference(value="/slide/whole_neg_area")
        insert_neg_area.set_params(operation_type=insert_neg_area.OPERATION_TYPE.INSERT, index=7)
        insert_neg_area.set_outputs(result="/slide/stats_image")
        
        insert_analysis_area = operators.simple.iterable.Manipulation(self)
        insert_analysis_area.set_inputs(iterable="/slide/stats_image")
        insert_analysis_area.set_params_reference(value="/slide/whole_analysis_area")
        insert_analysis_area.set_params(operation_type=insert_analysis_area.OPERATION_TYPE.INSERT, index=8)
        insert_analysis_area.set_outputs(result="/slide/stats_image")
    
        #cast list to array
        list = operators.conversion.CastArray(self)
        list.set_inputs(data= "/slide/stats_image")
        list.set_outputs(array="/slide/stats_image")
        list.set_params(node_type=list.NODE_TYPE.TENSOR)
        
        # Upload calculated stats.
        upload = operators.image_dx.properties.Upload(self)
        upload.set_inputs(properties="/slide/stats_image")
        upload.set_params(
            names=[
                   "Total Cell Count",
                   "CD8 Positive Count",
                   "CD8 Negative Count",
                   "Percent CD8 Positive",
                   "Cell area (um^2)",
                   "Positive Cell Density (count/cell area mm^2)",
                   "Positive Cell area (um^2)",
                   "Negative Cells area (um^2)",
                   "Analysis Area (um^2)",
                   ],
            type=upload.TYPE.IMAGE,
            override=True,
        )
