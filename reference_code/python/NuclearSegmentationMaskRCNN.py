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
# MASKRCNN_MODEL_PATH = Path("configs/model/panck-cd8-nuc-seg/panck-cd8-2804.ckpt")
# MASKRCNN_MODEL_CONFIG = Path("configs/model/panck-cd8-nuc-seg/panck-cd8-1024.yaml")

MASKRCNN_MODEL_CONFIG = Path("/Users/Downloads/configs_model_maskrcnn_v0.2.yaml")
MASKRCNN_MODEL_PATH = Path("/Users/Downloads/configs_model_cellseg_v0.2.pth")
REGION_TERMS = ["Parent"]
NUCLEUS_TERM = "maskrcnn_test"
CLASS_TERMS_TO_CLASS_IDS = {
    "maskrcnn_test": 1,
    "positive": 2,
}
#FEATURES_PATH = Path("C:/Users/Pranav/Documents/features/features01.csv")
TRAINING_CLASS_TERMS = list(CLASS_TERMS_TO_CLASS_IDS.keys())
DECOMPOSE_BASIS_VECTORS = QP_HDAB

class NuclearSegmentationThreshold(Pipe):

    Performs nuclear segmentation over given slide using the MASKRCNN model.
    Nuclei are filtered and a RandomForest classifier is applied to upload
    only CD8 positive cells to imageDx.

    :var slide_path: Path to the WSI file.
    :var project_id: ID of a study on imageDx.
    :var image_id: ID of an image from the imageDx study specified by the `project_id`.
    :var MASKRCNN_model_path: Path to the MASKRCNN model.
    :var MASKRCNN_model_config: Path to MASKRCNN config file.

    def __init__(self):
        super().__init__()

        # Special parameters.
        self.__slide_path = self._add_param(**special_params.slide_path)
        self.__project_id = self._add_param(**special_params.project_id)
        self.__image_id = self._add_param(**special_params.image_id)
        self.__size: int = self._add_param("size", int, 384)
        self.__stride: int = self._add_param("stride", int, 384)
        self.__zoom: int = self._add_param("zoom", int, 5)
        
        self.__decompose_basis_vectors = self._add_param(
            "decompose_basis_vectors", List[List[Number]], value=DECOMPOSE_BASIS_VECTORS
        )

        self.__MASKRCNN_model_path = self._add_param(
            "MASKRCNN_model_path", Path, required=True, value=MASKRCNN_MODEL_PATH
        )
        self.__MASKRCNN_model_config = self._add_param(
            "MASKRCNN_model_config", Path, required=True, value=MASKRCNN_MODEL_CONFIG
        )
        #self.__csv_mode = self._add_param("csv_mode", CsvMode, value=CsvMode.APPEND)
        #self.__features_path = self._add_param("features_path", Path, FEATURES_PATH)
        

    def create_pipeline(self):
        """
        Loads the slide and performs tissue segmentation using the `ActiveContours` subpipe
        and uploads obtained results on imageDX.
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

        NuclearSegmentationThreshold.image_stats(self)
        


    @staticmethod
    def prepare_data(self, attachment=None):
        """TODO"""

        microns = operators.general.ExtractProperty(self, attachment=attachment)
        microns.set_inputs(node="/slide")
        microns.set_params(property_names=microns.PROPERTY_NAMES.SLIDE.MPP_AVG)
        microns.set_outputs(attributes="/slide/mpp")

        read_region = operators.wsi.ReadRegion(self)
        read_region.set_inputs(slide="/slide")
        read_region.set_params(x=0, y=0, zoom=2)
        read_region.set_outputs(tile="/slide/ws_tile")

        load_annotations = operators.image_dx.annotations.Load(self)
        load_annotations.set_params_promotion(
            project_id="project_id",
            image_id="image_id",
        )
        load_annotations.set_params(
            annotation_type=load_annotations.ANNOTATION_TYPE.USER,
            terms=REGION_TERMS,
        )
        load_annotations.set_inputs(slide="/slide")
        load_annotations.set_outputs(
            mask="/slide/ws_tile/annotation", properties="/slide/ws_tile/annotation_properties"
        )

        shift = operators.mask.transformation.Rescale(self)
        shift.set_params(rescale_direction=shift.RESCALE_DIRECTION.SLIDE_TO_TILE)
        shift.set_inputs(mask="/slide/ws_tile/annotation")
        shift.set_outputs(mask="/slide/ws_tile/annotation")
        
        # #Iterate over each ROI
        # roi = operators.mask.general.Iterator(self)
        # #roi.set_params(mode=roi.MODE.GEOMETRY.POLYGON)
        # roi.set_inputs(mask="/slide/ws_tile/annotation")
        # roi.set_outputs(mask="/slide/ws_tile/annotation/block")
        

        
        # extract_property = operators.general.ExtractProperty(self)
        # extract_property.set_params(property_names=extract_property.PROPERTY_NAMES.MASK.LABELS)
        # extract_property.set_inputs(node="/slide/ws_tile/annotation")
        # extract_property.set_outputs(attributes="/slide/ws_tile/annotation/label")
        
        # # cast = operators.conversion.CastList(self)
        # # cast.set_inputs(data="/slide/ws_tile/annotation_properties")
        # # cast.set_outputs(list_data="/slide/ws_tile/annotation_properties")
        # data_printer = operators.debug.DataPrinter(self)
        # data_printer.set_inputs(args="/slide/ws_tile/annotation/label")
        
        # label_it = operators.array.Iterator(self)
        # label_it.set_inputs(array="/slide/ws_tile/annotation_properties")
        # label_it.set_params(axis=1)
        # label_it.set_outputs(element="/slide/ws_tile/annotation/label_it")
        
        # data_printer = operators.debug.DataPrinter(self)
        # data_printer.set_inputs(args="/slide/ws_tile/annotation_properties")
        
        area = operators.features.generation.Shape(self)
        area.set_inputs(mask="/slide/ws_tile/annotation")
        area.set_params(feature=area.FEATURE.AREA)
        area.set_outputs(features="/slide/target")
        
        # properties = operators.simple.dictionary.Manipulation(self)
        # properties.set_inputs(dictionary="/slide/ws_tile/annotation_properties")
        # properties.set_params(value=[],operation_type=properties.OPERATION_TYPE.EXTRACT)
        # properties.set_outputs("/slide/ws_tile/annotation_properties_key")
        
        # data_printer = operators.debug.DataPrinter(self)
        # data_printer.set_inputs(args="/slide/target")
        
        property_iterator = operators.array.Iterator(self)
        property_iterator.set_inputs(array="/slide/target")
        property_iterator.set_params(axis=0)
        property_iterator.set_outputs(element="/slide/target_element")
        
        data_printer = operators.debug.DataPrinter(self)
        data_printer.set_inputs(args="/slide/target_element")
        
        extract_id = operators.array.Manipulation(self)
        extract_id.set_inputs(array="/slide/target_element")
        extract_id.set_params(
            array_operation_type=extract_id.ARRAY_OPERATION_TYPE.EXTRACT, index=0, axis=0
        )
        extract_id.set_outputs(result="/slide/target/id")
        
        convert_id_to_int = operators.conversion.ConvertPrimitive(self)
        convert_id_to_int.set_inputs(node="/slide/target/id")
        convert_id_to_int.set_params(output_type=convert_id_to_int.OUTPUT_TYPE.INTEGER)
        convert_id_to_int.set_outputs(node="/slide/target/id")
        
        # data_printer555= operators.debug.DataPrinter(self)
        # data_printer555.set_inputs(args="/slide/target/id")
        
        
        # cast = operators.conversion.CastList(self)
        # cast.set_inputs(data="/slide/target/id")
        # cast.set_outputs(list_data="/slide/target/id_list")
        
        # data_printer555= operators.debug.DataPrinter(self)
        # data_printer555.set_inputs(args="/slide/target/id_list")
        
        # roi = operators.mask.general.Iterator(self)
        # roi.set_params_promotion(labels="slide/target/id")
        # roi.set_params(mode=roi.MODE.GEOMETRY.LABEL)
        # roi.set_inputs(mask="/slide/ws_tile/annotation")
        # roi.set_outputs(mask="/slide/ws_tile/annotation/block")
        
        roi = operators.mask.filtering.Labels(self)
        roi.set_params(operation_type=roi.OPERATION_TYPE.INCLUDE)
        roi.set_params_reference(labels="/slide/target/id")
        roi.set_inputs(mask="/slide/ws_tile/annotation")
        roi.set_outputs(mask="/slide/ws_tile/annotation/block")
        
        
        # plot_mask = operators.debug.ShowImage(self)
        # plot_mask.set_inputs(images=("/slide/ws_tile/annotation","/slide/ws_tile/annotation/block"))
        #operators.macro.DummyAggregator(self)
    @staticmethod
    def iterate(self):
        """
        Iterates slide over annotation mask, calls MASKRCNN on each tile.
        """
        #plot_mask = operators.debug.ShowImage(self)
        #plot_mask.set_inputs(images="/slide/ws_tile/annotation")
        read_region_iterator = operators.wsi.ReadRegionIterator(self)
        read_region_iterator.set_params(
            size=self.__size,
            zoom_type=read_region_iterator.ZOOM_TYPE.LEVEL,
            zoom=0,
            zct=[(0, 0, 0)],
            stride=self.__size - 80,
            threshold=0.01,
        )
        read_region_iterator.set_inputs(slide="/slide", mask="/slide/ws_tile/annotation/block")
        read_region_iterator.set_outputs(
            tile="/slide/rgb_region", intersection_mask="/slide/region_mask"
        )
        
        

    @staticmethod
    def segment(self):
        """
        MASKRCNN inference on RGB channel image. Multiplication step masks out nuclear predictions
        outside of imageDx annotation mask boundaries.
        """

        nuclear_segmentation = sub_pipes.nuclear_segmentation.NuclearSegmentationMaskRCNN(self)
        nuclear_segmentation.set_params_promotion(
            model_config="MASKRCNN_model_config",
            model_path="MASKRCNN_model_path",
            size = "size"
        )
        
        nuclear_segmentation.set_inputs(input_image="/slide/rgb_region")
        nuclear_segmentation.set_outputs(output_mask="/slide/rgb_region/MASKRCNN_mask")

        intersect = operators.mask.filtering.Intersection(self)
        intersect.set_inputs(
            mask="/slide/rgb_region/MASKRCNN_mask", filter_region="/slide/region_mask"
        )
        intersect.set_params(
            threshold_type=intersect.THRESHOLD_TYPE.CENTROID_DISTANCE, threshold=0, crop=False
        )
        intersect.set_outputs(filtered="/slide/rgb_region/MASKRCNN_region_mask")
        
        
    @staticmethod
    def filter(self):
        """TODO."""
        #Decompose Image and Extract Dab Channel to data container 
        decompose = operators.image.general.Decompose(self)
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
        
        #show_image = operators.debug.ShowImage(self)
        #show_image.set_inputs(images=("/slide/rgb_region/alpha","/slide/rgb_region/alpha0"))
        #show_image.set_params(viewer=show_image.VIEWER.MATPLOTLIB)
        
        #Calculate Features of Dab channel using MASKRCNN masks
        features = operators.features.generation.Intensity(self)
        features.set_inputs(mask="/slide/rgb_region/MASKRCNN_region_mask", image="/slide/rgb_region/alpha0")
        features.set_params(feature=[features.FEATURE.PERCENTILE_99])
        features.set_outputs(features="/slide/rgb_region/features")
        
        #data_printer = operators.debug.DataPrinter(self)
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
        
        #Filter the MASKRCNN mask to include only extracted labels
        filter_cells_pos = operators.mask.filtering.Labels(self)
        filter_cells_pos.set_inputs(mask="/slide/rgb_region/MASKRCNN_region_mask")
        filter_cells_pos.set_params(operation_type=filter_cells_pos.OPERATION_TYPE.INCLUDE)
        filter_cells_pos.set_params_reference(labels="/labels")
        filter_cells_pos.set_outputs(mask="/slide/rgb_region/MASKRCNN_region_mask_pos")
        
        #Extract the labels of the negative filtered data set
        extract_labels = operators.array.Manipulation(self)
        extract_labels.set_params(
        index=0,
        axis=1,
        array_operation_type=extract_labels.ARRAY_OPERATION_TYPE.EXTRACT,
    )
        extract_labels.set_inputs(array="/slide/rgb_region/filtered_features_neg")
        extract_labels.set_outputs(result="/labels_neg")
        
        #Filter the MASKRCNN mask to include only negative extracted labels
        filter_cells_neg = operators.mask.filtering.Labels(self)
        filter_cells_neg.set_inputs(mask="/slide/rgb_region/MASKRCNN_region_mask")
        filter_cells_neg.set_params(operation_type=filter_cells_pos.OPERATION_TYPE.INCLUDE)
        filter_cells_neg.set_params_reference(labels="/labels_neg")
        filter_cells_neg.set_outputs(mask="/slide/rgb_region/MASKRCNN_region_mask_neg")
        
        """
        Block of operators that convert input and write feature values into the .csv file.
        """
        # manipulation_extract = operators.array.Manipulation(self)
        # manipulation_extract.set_params(
        #     array_operation_type=manipulation_extract.ARRAY_OPERATION_TYPE.EXTRACT,
        #     index=1,
        #     axis=1,
        # )
        # manipulation_extract.set_inputs(array="/slide/rgb_region/features")
        # manipulation_extract.set_outputs(result="/slide/rgb_region/features_ex")
        
        # data_printer = operators.debug.DataPrinter(self)
        # data_printer.set_inputs(args="/slide/rgb_region/features_ex")

        # convert_list = operators.conversion.CastList(self)
        # convert_list.set_inputs(data="/slide/rgb_region/features")
        # convert_list.set_outputs(list_data="/slide/rgb_region/features_csv")
        
        # data_printer = operators.debug.DataPrinter(self)
        # data_printer.set_inputs(args="/slide/rgb_region/features_csv")

        # csv_write = operators.io.csv.Write(self)
        # csv_write.set_params(columns=['label','Intensity'])
        # csv_write.set_params_promotion(
        #     path="features_path",
        #     mode="csv_mode",
        # )
        # csv_write.set_inputs(data="/slide/rgb_region/features_csv")

    @staticmethod
    def aggregate(self):
        """TODO."""
        # Aggregate and passthrough MASKRCNN mask
        nucleus_agg = operators.mask.general.Aggregator(self)
        nucleus_agg.set_params(merge=False, rescale=True)
        nucleus_agg.set_inputs(mask="/slide/rgb_region/MASKRCNN_region_mask")
        nucleus_agg.set_outputs(mask="/slide/aggregated_MASKRCNN_mask")
        nucleus_agg.set_mode(mode=AggregationMode.PASSTHROUGH)

        # Aggregate and passthrough MASKRCNN mask of positive cells
        nucleus_pos_agg = operators.mask.general.Aggregator(self)
        nucleus_pos_agg.set_params(merge=False, rescale=True)
        nucleus_pos_agg.set_inputs(mask="/slide/rgb_region/MASKRCNN_region_mask_pos")
        nucleus_pos_agg.set_outputs(mask="/slide/aggregated_MASKRCNN_mask_pos")
        nucleus_pos_agg.set_mode(mode=AggregationMode.PASSTHROUGH)
       
        #Aggregate and close MASKRCNN mask of negative cells
        nucleus_neg_agg = operators.mask.general.Aggregator(self)
        nucleus_neg_agg.set_params(merge=False, rescale=True)
        nucleus_neg_agg.set_inputs(mask="/slide/rgb_region/MASKRCNN_region_mask_neg")
        nucleus_neg_agg.set_outputs(mask="/slide/aggregated_MASKRCNN_mask_neg")
        
        NuclearSegmentationThreshold.statsperblock(self)
        #close id iterator
        nucleus_neg_agg = operators.simple.iterable.Aggregator(self)
        nucleus_neg_agg.set_inputs(node="/slide/target/id")
        nucleus_neg_agg.set_outputs(result="/slide/target/id_agg")
        
        # #Closes annotation iterator
        # nucleus_neg_agg = operators.mask.general.Aggregator(self)
        # nucleus_neg_agg.set_params(merge=False, rescale=True)
        # nucleus_neg_agg.set_inputs(mask="/slide/ws_tile/annotation/block")
        # nucleus_neg_agg.set_outputs(mask="/slide/ws_tile/annotation/agg_block")
        
        #masking postprocessing
        nms = operators.deep_learning.postprocessing.NonMaximumSuppression(self)
        nms.set_inputs(mask="/slide/aggregated_MASKRCNN_mask")
        nms.set_params(iou_threshold=0.40, metric=nms.METRIC.INTERSECTION_OVER_SMALLER_AREA)
        nms.set_outputs(mask="/slide/aggregated_MASKRCNN_mask")

        nms = operators.deep_learning.postprocessing.NonMaximumSuppression(self)
        nms.set_inputs(mask="/slide/aggregated_MASKRCNN_mask_pos")
        nms.set_params(iou_threshold=0.40, metric=nms.METRIC.INTERSECTION_OVER_SMALLER_AREA)
        nms.set_outputs(mask="/slide/aggregated_MASKRCNN_mask_pos")
        
        nms = operators.deep_learning.postprocessing.NonMaximumSuppression(self)
        nms.set_inputs(mask="/slide/aggregated_MASKRCNN_mask_neg")
        nms.set_params(iou_threshold=0.40, metric=nms.METRIC.INTERSECTION_OVER_SMALLER_AREA)
        nms.set_outputs(mask="/slide/aggregated_MASKRCNN_mask_neg")
        

    @staticmethod
    def clear_data(self):
        """TODO."""
        # Delete Nuclus and Positive Terms
        delete = operators.image_dx.annotations.Delete(self)
        delete.set_inputs(slide="/slide")
        delete.set_params(terms=[NUCLEUS_TERM,'positive'])
        # #Upload positive masks with Positive term
        # uploader = operators.image_dx.annotations.Upload(self)
        # uploader.set_params(terms='positive')
        # uploader.set_inputs(mask="/slide/aggregated_MASKRCNN_mask_pos", slide="/slide")
        # #Upload Negative mask with Nucleus term
        # uploader = operators.image_dx.annotations.Upload(self)
        # uploader.set_params(terms=NUCLEUS_TERM)
        # uploader.set_inputs(mask="/slide/aggregated_MASKRCNN_mask_neg", slide="/slide")

        #return uploader
    
    @staticmethod
    def statsperblock(self):
        #Extract positive cell counts
        extract_pos_annotation_count = operators.general.ExtractProperty(self)
        extract_pos_annotation_count.set_params(
            property_names=extract_pos_annotation_count.PROPERTY_NAMES.MASK.COUNT
        )
        extract_pos_annotation_count.set_inputs(node="/slide/aggregated_MASKRCNN_mask_pos")
        extract_pos_annotation_count.set_outputs(attributes="/slide/annotation_pos_count")
        #Extract Negative cell counts
        extract_neg_annotation_count = operators.general.ExtractProperty(self)
        extract_neg_annotation_count.set_params(
            property_names=extract_neg_annotation_count.PROPERTY_NAMES.MASK.COUNT
        )
        extract_neg_annotation_count.set_inputs(node="/slide/aggregated_MASKRCNN_mask_neg")
        extract_neg_annotation_count.set_outputs(attributes="/slide/annotation_neg_count")
        #Extract total cell counts
        extract_annotation_count = operators.general.ExtractProperty(self)
        extract_annotation_count.set_params(
            property_names=extract_annotation_count.PROPERTY_NAMES.MASK.COUNT
        )
        extract_annotation_count.set_inputs(node="/slide/aggregated_MASKRCNN_mask")
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
        # #calculate CD8 area
        # extract_cd8_area_in_pixels = operators.general.ExtractProperty(self)
        # extract_cd8_area_in_pixels.set_inputs(node="/slide/aggregated_MASKRCNN_mask_pos")
        # extract_cd8_area_in_pixels.set_params(
        #     property_names=extract_cd8_area_in_pixels.PROPERTY_NAMES.MASK.AREA
        # )
        # extract_cd8_area_in_pixels.set_outputs(attributes="/slide/cd8_area")
        
        # data_printer = operators.debug.DataPrinter(self)
        # data_printer.set_inputs (args="/slide/cd8_area")
        
        #Insert stats to node 
        put_empty_simple = operators.simple.general.Put(self)
        put_empty_simple.set_params(value=[])
        put_empty_simple.set_outputs(data="/slide/stats")
        
        insert_cd8_neg_counts = operators.simple.iterable.Manipulation(self)
        insert_cd8_neg_counts.set_inputs(iterable="/slide/stats")
        insert_cd8_neg_counts.set_params_reference(value="/slide/annotation_neg_count")
        insert_cd8_neg_counts.set_params(operation_type=insert_cd8_neg_counts.OPERATION_TYPE.INSERT, index=0)
        insert_cd8_neg_counts.set_outputs(result="/slide/stats")
        
        insert_cd8_counts = operators.simple.iterable.Manipulation(self)
        insert_cd8_counts.set_inputs(iterable="/slide/stats")
        insert_cd8_counts.set_params_reference(value="/slide/annotation_pos_count")
        insert_cd8_counts.set_params(operation_type=insert_cd8_counts.OPERATION_TYPE.INSERT, index=1)
        insert_cd8_counts.set_outputs(result="/slide/stats")
        
        insert_cd8_percent = operators.simple.iterable.Manipulation(self)
        insert_cd8_percent.set_inputs(iterable="/slide/stats")
        insert_cd8_percent.set_params_reference(value="/slide/percent_pos")
        insert_cd8_percent.set_params(operation_type=insert_cd8_percent.OPERATION_TYPE.INSERT, index=2)
        insert_cd8_percent.set_outputs(result="/slide/stats")
    
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
            names=["CD8 Negative","CD8 Positive Counts","Percent CD8 Positive"],
            type=upload.TYPE.ANNOTATION,
            override=True,

        )
        #Upload positive masks with Positive term
        uploader = operators.image_dx.annotations.Upload(self)
        uploader.set_params(terms='positive')
        uploader.set_inputs(mask="/slide/aggregated_MASKRCNN_mask_pos", slide="/slide")
        #Upload Negative mask with Nucleus term
        uploader = operators.image_dx.annotations.Upload(self)
        uploader.set_params(terms=NUCLEUS_TERM)
        uploader.set_inputs(mask="/slide/aggregated_MASKRCNN_mask_neg", slide="/slide")
        
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
        
        # plot = operators.debug.ShowImage(self)
        # plot.set_inputs(images="/slide/whole_pos")
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
        
        
        # extract_annotation_count = operators.general.ExtractProperty(self)
        # extract_annotation_count.set_params(
        #     property_names=extract_annotation_count.PROPERTY_NAMES.MASK.COUNT
        # )
        # extract_annotation_count.set_inputs(node="/slide/aggregated_MASKRCNN_mask")
        # extract_annotation_count.set_outputs(attributes="/slide/annotation_count")
        
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
        # #calculate CD8 area
        # extract_cd8_area_in_pixels = operators.general.ExtractProperty(self)
        # extract_cd8_area_in_pixels.set_inputs(node="/slide/aggregated_MASKRCNN_mask_pos")
        # extract_cd8_area_in_pixels.set_params(
        #     property_names=extract_cd8_area_in_pixels.PROPERTY_NAMES.MASK.AREA
        # )
        # extract_cd8_area_in_pixels.set_outputs(attributes="/slide/cd8_area")
        
        # data_printer = operators.debug.DataPrinter(self)
        # data_printer.set_inputs (args="/slide/cd8_area")
        
        #Insert stats to node 
        put_empty_simple = operators.simple.general.Put(self)
        put_empty_simple.set_params(value=[])
        put_empty_simple.set_outputs(data="/slide/stats")
        
        insert_cd8_neg_counts = operators.simple.iterable.Manipulation(self)
        insert_cd8_neg_counts.set_inputs(iterable="/slide/stats")
        insert_cd8_neg_counts.set_params_reference(value="/slide/whole_neg_count")
        insert_cd8_neg_counts.set_params(operation_type=insert_cd8_neg_counts.OPERATION_TYPE.INSERT, index=0)
        insert_cd8_neg_counts.set_outputs(result="/slide/stats")
        
        insert_cd8_counts = operators.simple.iterable.Manipulation(self)
        insert_cd8_counts.set_inputs(iterable="/slide/stats")
        insert_cd8_counts.set_params_reference(value="/slide/whole_pos_count")
        insert_cd8_counts.set_params(operation_type=insert_cd8_counts.OPERATION_TYPE.INSERT, index=1)
        insert_cd8_counts.set_outputs(result="/slide/stats")
        
        insert_cd8_percent = operators.simple.iterable.Manipulation(self)
        insert_cd8_percent.set_inputs(iterable="/slide/stats")
        insert_cd8_percent.set_params_reference(value="/slide/whole_percent_pos")
        insert_cd8_percent.set_params(operation_type=insert_cd8_percent.OPERATION_TYPE.INSERT, index=2)
        insert_cd8_percent.set_outputs(result="/slide/stats")
    
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
        upload.set_params(
            names=["CD8 Negative","CD8 Positive Counts","Percent CD8 Positive"],
            type=upload.TYPE.IMAGE,
            override=True,
        )
