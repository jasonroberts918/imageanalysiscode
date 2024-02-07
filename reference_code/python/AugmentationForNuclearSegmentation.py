# ppcli run .\projects\nuclear_augmentation\nuclear_segmentation_save.py

import os

import numpy as np
import skimage.io
from pipeline_processor.core.data.data_node.simple_node import SimpleNode
from py_pipeline import operators, sub_pipes
from py_pipeline.core import Pipe, special_params
from py_pipeline.data import QP_HDAB, Path

# Image and mask
SLIDE = "slides/slide"
PROJECT_ID = 111
IMAGE_ID = 111
TERM = "tissue"
NUCLEUS = "cell"
TILE_SIZE = 544
TILE_STRIDE = 272
TILE_THD = 0.3
DOWNSAMPLE = 1

# DAB nuclear segmentation
DAB_CENTERS_THD = 0.5
DAB_NMS_KERNEL_SIZE = 7
DAB_AREA = 200
DAB_MEADIAN = 100
DAB_CIRC = 0.5

# Hematoxylin nuclear segmentation
HEM_CENTERS_THD = 0.5
HEM_NMS_KERNEL_SIZE = 7
HEM_AREA = 150
HEM_AREA_GT = 1000
HEM_MEADIAN = 50
HEM_CIRC = 0.3

# Post-join filter
ALL_AREA = 200
ALL_CIRC = 1.0

# Other
SHOW_ALL = False

# Editing
EDIT = False

# Ne diraj
OUTPUT = "nucseg/" + SLIDE.split("/")[-1].split(".")[0]
COUNTER = 0


def new_filename(args):
    global COUNTER, OUTPUT

    os.makedirs(Path(OUTPUT).path, exist_ok=True)

    mask = args[0].data
    tile = args[1].data

    mask_unique = np.unique(mask)
    if list(mask_unique) != list(range(len(mask_unique))):
        for i, j in zip(list(mask_unique), range(len(mask_unique))):
            mask[mask == i] = j

    np.save(Path(OUTPUT + "/" + str(COUNTER) + "_mask.npy").path, mask)
    np.save(Path(OUTPUT + "/" + str(COUNTER) + "_tile.npy").path, tile)

    skimage.io.imsave(Path(OUTPUT + "/" + str(COUNTER) + "_mask.png").path, mask.squeeze())
    skimage.io.imsave(Path(OUTPUT + "/" + str(COUNTER) + "_tile.png").path, tile)

    COUNTER += 1


def user_input_binary(args):
    a = input(
        "If detections are not good, type anything and press Enter; otherwise just press Enter: "
    )

    result = len(a) != 0
    result = SimpleNode(result)

    return (result,)


def user_input_unary(args):
    a = input("Press Enter when you're done editing the annotations.")


class NuclearSegmentationExample(Pipe):


    def __init__(self):
        super().__init__()

        # Spetial parameters.
        self.__slide_path = self._add_param(**special_params.slide_path, value=Path(SLIDE))
        self.__project_id = self._add_param(**special_params.project_id, value=PROJECT_ID)
        self.__image_id = self._add_param(**special_params.image_id, value=IMAGE_ID)

    def create_pipeline(self):
        # Prepare input data.
        self.load_tile()
        self.color_deconvolution()

        # Segment and filter nuclei.
        # self.segment_nuclei_dab()
        # self.filter_nuclei_dab()
        self.segment_nuclei_hem()
        self.filter_nuclei_hem()

        # join_masks = operators.mask.general.Join(self)
        # join_masks.set_inputs(masks=("/slide/tile/mask_dab_filtered", "/slide/tile/mask_hem_filtered"))
        # join_masks.set_outputs(result="/slide/tile/mask_filtered")

        # self.filter_all()

        dup = operators.general.DuplicateNode(self)
        dup.set_inputs(node="/slide/tile/mask_hem_filtered")
        dup.set_outputs(duplicate="/slide/tile/mask_filtered")

        self.display_segmentation()

        # Manual editting.
        if EDIT:
            self.manual_edit()

        # Save results.
        self.save_result()

        # Close loop started in load tile.
        operators.general.DummyAggregator(self)

    def load_tile(self):
        """
        Load a whole slide image and read a tile from it.
        """

        put_empty = operators.array.Put(self)
        put_empty.set_params(value=np.zeros((544, 544, 1), dtype=np.uint8))
        put_empty.set_outputs(tensor="/empty_tile")

        conv_mask = operators.conversion.ConvertArray(self)
        conv_mask.set_inputs(array="/empty_tile")
        conv_mask.set_params(array_node_type=conv_mask.ARRAY_NODE_TYPE.MASK)
        conv_mask.set_outputs(output="/empty_tile")

        load_slide = operators.wsi.LoadSlide(self)
        load_slide.set_params_promotion(
            slide_path="slide_path", project_id="project_id", image_id="image_id"
        )
        load_slide.set_outputs(slide="/slide")

        if DOWNSAMPLE is None:
            extract_mpp = operators.general.ExtractProperty(self)
            extract_mpp.set_inputs(node="/slide")
            extract_mpp.set_params(property_names=extract_mpp.PROPERTY_NAMES.SLIDE.MPP_AVG)
            extract_mpp.set_outputs(attributes="/slide/mpp")

            calculate_optimal_downsample = operators.simple.numeric.Math(self)
            calculate_optimal_downsample.set_inputs(data1_operand="/slide/mpp")
            calculate_optimal_downsample.set_params(
                operation_type=calculate_optimal_downsample.OPERATION_TYPE.UNARY.MULTIPLICATIVE_INVERSE
            )
            calculate_optimal_downsample.set_outputs(result="/slide/optimal_downsample")

            operators.macro.DataPrinter(self, args="/slide/optimal_downsample")
        else:
            put = operators.simple.general.Put(self)
            put.set_params(value=DOWNSAMPLE)
            put.set_outputs(data="/slide/optimal_downsample")

        load_tissue = operators.image_dx.annotations.Load(self)
        load_tissue.set_inputs(slide="/slide")
        load_tissue.set_params(
            annotation_type=load_tissue.ANNOTATION_TYPE.USER,
            config_user_annotations=True,
            terms=[TERM],
        )
        load_tissue.set_outputs(mask="/slide/tissue")

        read_region = operators.wsi.ReadRegionIterator(self)
        read_region.set_inputs(slide="/slide", mask="/slide/tissue")
        read_region.set_params(
            size=TILE_SIZE,
            stride=TILE_STRIDE,
            zoom_type=read_region.ZOOM_TYPE.DOWNSAMPLE,
            threshold=TILE_THD,
        )
        read_region.set_params_reference(zoom="/slide/optimal_downsample")
        read_region.set_outputs(tile="tile")

    def color_deconvolution(self):
        """
        Deconvolve tile and extract the nuclei channel.
        """

        deconvolve = operators.image.stain.ColorDeconvolution(self)
        deconvolve.set_inputs(image="/slide/tile")
        deconvolve.set_params(
            stain_matrix=QP_HDAB,
            background_intensity=(255, 255, 255),
        )
        deconvolve.set_outputs(stains="stains")

        extract_nuclei_channel = operators.array.Manipulation(self)
        extract_nuclei_channel.set_inputs(array="stains")
        extract_nuclei_channel.set_params(
            array_operation_type=extract_nuclei_channel.ARRAY_OPERATION_TYPE.EXTRACT,
            index=1,
            axis=-1,
        )
        extract_nuclei_channel.set_outputs(result="dab")

        extract_nuclei_channel = operators.array.Manipulation(self)
        extract_nuclei_channel.set_inputs(array="/slide/tile/stains")
        extract_nuclei_channel.set_params(
            array_operation_type=extract_nuclei_channel.ARRAY_OPERATION_TYPE.EXTRACT,
            index=0,
            axis=-1,
        )
        extract_nuclei_channel.set_outputs(result="/slide/tile/blue")

        invert_nuclei_channel = operators.array.Math(self)
        invert_nuclei_channel.set_inputs(array_1="/slide/tile/stains/dab")
        invert_nuclei_channel.set_params(
            operation_type=invert_nuclei_channel.OPERATION_TYPE.UNARY.INVERSE_SUBTRACTION
        )
        invert_nuclei_channel.set_outputs(array="../dab_inv")

        # extract_nuclei_channel = operators.array.Manipulation(self)
        # extract_nuclei_channel.set_inputs(array="/slide/tile")
        # extract_nuclei_channel.set_params(
        #     array_operation_type=extract_nuclei_channel.ARRAY_OPERATION_TYPE.EXTRACT,
        #     index=2,
        #     axis=-1,
        # )
        # extract_nuclei_channel.set_outputs(result="blue")

        gray = operators.image.general.ConvertColorSpace(self)
        gray.set_inputs(image="/slide/tile")
        gray.set_params(output_color_space=gray.OUTPUT_COLOR_SPACE.GRAY)
        gray.set_outputs(converted_image="/slide/tile/blue")

        invert_nuclei_channel = operators.array.Math(self)
        invert_nuclei_channel.set_inputs(array_1="/slide/tile/blue")
        invert_nuclei_channel.set_params(
            operation_type=invert_nuclei_channel.OPERATION_TYPE.UNARY.INVERSE_SUBTRACTION
        )
        invert_nuclei_channel.set_outputs(array="/slide/tile/blue")

    def segment_nuclei_dab(self):
        """
        Segment nuclei on the deconvolved tile inverted nuclei channel.
        """

        star_dist = sub_pipes.nuclear_segmentation.NuclearSegmentationStarDistIF(self)
        star_dist.set_inputs(input_image="/slide/tile/stains/dab_inv")
        star_dist.set_params(
            model_path=Path("models/stardist/32_2D_versatile_fluo.pth"),
            model_config=Path("models/stardist/32_star_dist_sa_orig_tezinama_fluo.yaml"),
            centers_threshold=DAB_CENTERS_THD,
            nms_kernel_size=DAB_NMS_KERNEL_SIZE,
        )
        star_dist.set_outputs(output_mask="/slide/tile/mask_dab")

    def segment_nuclei_hem(self):
        """
        Segment nuclei on the deconvolved tile inverted nuclei channel.
        """

        star_dist = sub_pipes.nuclear_segmentation.NuclearSegmentationStarDistIF(self)
        star_dist.set_inputs(input_image="/slide/tile/blue")
        star_dist.set_params(
            model_path=Path("models/stardist/32_2D_versatile_fluo.pth"),
            model_config=Path("models/stardist/32_star_dist_sa_orig_tezinama_fluo.yaml"),
            centers_threshold=HEM_CENTERS_THD,
            nms_kernel_size=HEM_NMS_KERNEL_SIZE,
        )
        star_dist.set_outputs(output_mask="/slide/tile/mask_hem")

    def filter_nuclei_dab(self):
        """
        Filter detections.
        """

        isempty = operators.general.ExtractProperty(self)
        isempty.set_inputs(node="/slide/tile/mask_dab")
        isempty.set_params(property_names=isempty.PROPERTY_NAMES.MASK.IS_EMPTY)
        isempty.set_outputs(attributes="/slide/tile/mask_dab/is_empty")

        ifelse = operators.branching.IfElse(self)
        ifelse.set_inputs(flag="/slide/tile/mask_dab/is_empty")

        shape_features = operators.features.generation.Shape(self, (ifelse, False))
        shape_features.set_inputs(mask="/slide/tile/mask_dab")
        shape_features.set_params(
            feature=[shape_features.FEATURE.AREA, shape_features.FEATURE.CIRCULARITY]
        )
        shape_features.set_outputs(features="/slide/tile/mask_dab/feautres_shape")

        intensity_features = operators.features.generation.Intensity(self)
        intensity_features.set_inputs(
            mask="/slide/tile/mask_dab", image="/slide/tile/stains/dab_inv"
        )
        intensity_features.set_params(
            feature=[intensity_features.FEATURE.MEDIAN]
        )
        intensity_features.set_outputs(features="/slide/tile/mask_dab/feautres_intensity")

        merge_features = operators.features.general.Merge(self)
        merge_features.set_inputs(
            first="/slide/tile/mask_dab/feautres_shape", second="/slide/tile/mask_dab/feautres_intensity"
        )
        merge_features.set_outputs(features="/slide/tile/mask_dab/features")

        filter_array = operators.array.Filter(self)
        filter_array.set_inputs(array="/slide/tile/mask_dab/features")
        filter_array.set_params(
            operation_type=filter_array.OPERATION_TYPE.EXCLUDE,
            index=[1, 2, 3],
            compare_type=[filter_array.COMPARE_TYPE.LESS_THAN, filter_array.COMPARE_TYPE.LESS_THAN, filter_array.COMPARE_TYPE.LESS_THAN],
            threshold=[DAB_AREA, DAB_CIRC, DAB_MEADIAN],
            axis=1,
            filter_type=filter_array.FILTER_TYPE.ANY,
        )
        filter_array.set_outputs(array="/slide/tile/mask_dab/features_filtered")

        extr_size = operators.general.ExtractProperty(self)
        extr_size.set_inputs(node="/slide/tile/mask_dab/features_filtered")
        extr_size.set_params(property_names=[extr_size.PROPERTY_NAMES.TENSOR.SIZE])
        extr_size.set_outputs(attributes="/slide/tile/mask_dab/features_filtered/size")

        conv_prim = operators.conversion.ConvertPrimitive(self)
        conv_prim.set_inputs(node="/slide/tile/mask_dab/features_filtered/size")
        conv_prim.set_params(output_type=conv_prim.OUTPUT_TYPE.BOOLEAN)
        conv_prim.set_outputs(node="/slide/tile/mask_dab/features_filtered/size")

        ifelse2 = operators.branching.IfElse(self)
        ifelse2.set_inputs(flag="/slide/tile/mask_dab/features_filtered/size")

        extract_labels = operators.array.Manipulation(self, (ifelse2, True))
        extract_labels.set_inputs(array="/slide/tile/mask_dab/features_filtered")
        extract_labels.set_params(
            index=0, axis=1, array_operation_type=extract_labels.ARRAY_OPERATION_TYPE.EXTRACT
        )
        extract_labels.set_outputs(result="/slide/tile/mask_dab/features_filtered_labels")

        filter_mask = operators.mask.filtering.Labels(self)
        filter_mask.set_inputs(mask="/slide/tile/mask_dab")
        filter_mask.set_params(operation_type=filter_mask.OPERATION_TYPE.INCLUDE)
        filter_mask.set_params_reference(labels="/slide/tile/mask_dab/features_filtered_labels")
        filter_mask.set_outputs(mask="/slide/tile/mask_dab_filtered")

        duplicate = operators.general.DuplicateNode(self, (ifelse2, False))
        duplicate.set_inputs(node="/empty_tile")
        duplicate.set_outputs(duplicate="/slide/tile/mask_dab_filtered")

        join = operators.branching.Join(self, [duplicate, filter_mask])

        duplicate = operators.general.DuplicateNode(self, (ifelse, True))
        duplicate.set_inputs(node="/slide/tile/mask_dab")
        duplicate.set_outputs(duplicate="/slide/tile/mask_dab_filtered")

        operators.branching.Join(self, [duplicate, join])

    def filter_nuclei_hem(self):
        """
        Filter detections.
        """

        isempty = operators.general.ExtractProperty(self)
        isempty.set_inputs(node="/slide/tile/mask_hem")
        isempty.set_params(property_names=isempty.PROPERTY_NAMES.MASK.IS_EMPTY)
        isempty.set_outputs(attributes="/slide/tile/mask_hem/is_empty")

        ifelse = operators.branching.IfElse(self)
        ifelse.set_inputs(flag="/slide/tile/mask_hem/is_empty")

        shape_features = operators.features.generation.Shape(self, (ifelse, False))
        shape_features.set_inputs(mask="/slide/tile/mask_hem")
        shape_features.set_params(
            feature=[shape_features.FEATURE.AREA, shape_features.FEATURE.PERIMETER, shape_features.FEATURE.CIRCULARITY]
        )
        shape_features.set_outputs(features="/slide/tile/mask_hem/feautres_shape")

        intensity_features = operators.features.generation.Intensity(self)
        intensity_features.set_inputs(
            mask="/slide/tile/mask_hem", image="/slide/tile/blue"
        )
        intensity_features.set_params(
            feature=[intensity_features.FEATURE.MEDIAN]
        )
        intensity_features.set_outputs(features="/slide/tile/mask_hem/feautres_intensity")

        merge_features = operators.features.general.Merge(self)
        merge_features.set_inputs(
            first="/slide/tile/mask_hem/feautres_shape", second="/slide/tile/mask_hem/feautres_intensity"
        )
        merge_features.set_outputs(features="/slide/tile/mask_hem/features")

        filter_array = operators.array.Filter(self)
        filter_array.set_inputs(array="/slide/tile/mask_hem/features")
        filter_array.set_params(
            operation_type=filter_array.OPERATION_TYPE.EXCLUDE,
            index=[1, 2, 3, 4],
            compare_type=[filter_array.COMPARE_TYPE.LESS_THAN, filter_array.COMPARE_TYPE.GREATER_THAN, filter_array.COMPARE_TYPE.LESS_THAN, filter_array.COMPARE_TYPE.LESS_THAN],
            threshold=[HEM_AREA, HEM_AREA_GT, HEM_CIRC, HEM_MEADIAN],
            axis=1,
            filter_type=filter_array.FILTER_TYPE.ANY,
        )
        filter_array.set_outputs(array="/slide/tile/mask_hem/features_filtered")

        extr_size = operators.general.ExtractProperty(self)
        extr_size.set_inputs(node="/slide/tile/mask_hem/features_filtered")
        extr_size.set_params(property_names=[extr_size.PROPERTY_NAMES.TENSOR.SIZE, extr_size.PROPERTY_NAMES.TENSOR.SHAPE])
        extr_size.set_outputs(attributes=("/slide/tile/mask_hem/features_filtered/size", "/slide/tile/mask_hem/features_filtered/shape"))

        conv_prim = operators.conversion.ConvertPrimitive(self)
        conv_prim.set_inputs(node="/slide/tile/mask_hem/features_filtered/size")
        conv_prim.set_params(output_type=conv_prim.OUTPUT_TYPE.BOOLEAN)
        conv_prim.set_outputs(node="/slide/tile/mask_hem/features_filtered/size")

        ifelse2 = operators.branching.IfElse(self)
        ifelse2.set_inputs(flag="/slide/tile/mask_hem/features_filtered/size")

        extract_labels = operators.array.Manipulation(self, (ifelse2, True))
        extract_labels.set_inputs(array="/slide/tile/mask_hem/features_filtered")
        extract_labels.set_params(
            index=0, axis=1, array_operation_type=extract_labels.ARRAY_OPERATION_TYPE.EXTRACT
        )
        extract_labels.set_outputs(result="/slide/tile/mask_hem/features_filtered_labels")

        filter_mask = operators.mask.filtering.Labels(self)
        filter_mask.set_inputs(mask="/slide/tile/mask_hem")
        filter_mask.set_params(operation_type=filter_mask.OPERATION_TYPE.INCLUDE)
        filter_mask.set_params_reference(labels="/slide/tile/mask_hem/features_filtered_labels")
        filter_mask.set_outputs(mask="/slide/tile/mask_hem_filtered")

        duplicate = operators.general.DuplicateNode(self, (ifelse2, False))
        duplicate.set_inputs(node="/empty_tile")
        duplicate.set_outputs(duplicate="/slide/tile/mask_hem_filtered")

        join = operators.branching.Join(self, [duplicate, filter_mask])

        duplicate = operators.general.DuplicateNode(self, (ifelse, True))
        duplicate.set_inputs(node="/slide/tile/mask_hem")
        duplicate.set_outputs(duplicate="/slide/tile/mask_hem_filtered")

        operators.branching.Join(self, [duplicate, join])

    def filter_all(self):
        isempty = operators.general.ExtractProperty(self)
        isempty.set_inputs(node="/slide/tile/mask_filtered")
        isempty.set_params(property_names=isempty.PROPERTY_NAMES.MASK.IS_EMPTY)
        isempty.set_outputs(attributes="/slide/tile/mask_filtered/is_empty")

        ifelse = operators.branching.IfElse(self)
        ifelse.set_inputs(flag="/slide/tile/mask_filtered/is_empty")

        shape_features = operators.features.generation.Shape(self, (ifelse, False))
        shape_features.set_inputs(mask="/slide/tile/mask_filtered")
        shape_features.set_params(
            feature=[shape_features.FEATURE.AREA, shape_features.FEATURE.CIRCULARITY]
        )
        shape_features.set_outputs(features="/slide/tile/mask_filtered/feautres_shape")

        filter_array = operators.array.Filter(self)
        filter_array.set_inputs(array="/slide/tile/mask_filtered/features_shape")
        filter_array.set_params(
            operation_type=filter_array.OPERATION_TYPE.EXCLUDE,
            index=[1, 2],
            compare_type=[filter_array.COMPARE_TYPE.LESS_THAN, filter_array.COMPARE_TYPE.LESS_THAN],
            threshold=[ALL_AREA, ALL_CIRC],
            axis=1,
            filter_type=filter_array.FILTER_TYPE.ANY,
        )
        filter_array.set_outputs(array="/slide/tile/mask_filtered/features_filtered")

        extract_labels = operators.array.Manipulation(self)
        extract_labels.set_inputs(array="/slide/tile/mask_filtered/features_filtered")
        extract_labels.set_params(
            index=0, axis=1, array_operation_type=extract_labels.ARRAY_OPERATION_TYPE.EXTRACT
        )
        extract_labels.set_outputs(result="/slide/tile/mask_filtered/features_filtered_labels")

        filter_mask = operators.mask.filtering.Labels(self)
        filter_mask.set_inputs(mask="/slide/tile/mask_filtered")
        filter_mask.set_params(operation_type=filter_mask.OPERATION_TYPE.INCLUDE)
        filter_mask.set_params_reference(labels="/slide/tile/mask_filtered/features_filtered_labels")
        filter_mask.set_outputs(mask="/slide/tile/mask_filtered")

        duplicate = operators.general.DuplicateNode(self, (ifelse, True))
        duplicate.set_inputs(node="/slide/tile/mask_filtered")
        duplicate.set_outputs(duplicate="/slide/tile/mask_filtered")

        operators.branching.Join(self, [duplicate, filter_mask])

    def display_segmentation(self):
        """
        Draw resulting mask onto the original tile and display images from each steps of the process.
        """

        draw_contours = operators.image.general.DrawContours(self)
        draw_contours.set_inputs(image="/slide/tile", masks="/slide/tile/mask_filtered")
        draw_contours.set_params(color=(0, 255, 0))
        draw_contours.set_outputs(contours_drawn_image="/slide/tile/with_contours")

        if SHOW_ALL:
            show_dab = operators.debug.ShowImage(self)
            show_dab.set_inputs(
                images=(
                    "/slide/tile",
                    "/slide/tile/stains/dab_inv",
                    "/slide/tile/mask_dab",
                    "/slide/tile/mask_dab_filtered",
                )
            )

            show_dab = operators.debug.ShowImage(self)
            show_dab.set_inputs(
                images=(
                    "/slide/tile",
                    "/slide/tile/blue",
                    "/slide/tile/mask_hem",
                    "/slide/tile/mask_hem_filtered",
                )
            )

        # show_dab = operators.debug.ShowImage(self)
        # show_dab.set_inputs(
        #     images="/slide/tile/with_contours"
        # )

        # show_dab = operators.debug.plotting.PlotMask(self)
        # show_dab.set_inputs(
        #     masks="/slide/tile/mask_filtered",
        #     background="/slide/tile",
        # )
        # show_dab.set_params(alpha=0.3, color="#00FF00")

    def manual_edit(self):
        """
        Upload annotations to imageDx, allow time for the user to edit them on imageDx before
        loading them again and deleting the from imageDx.
        """

        user_input = operators.debug.ExecuteMethod(self)
        user_input.set_params(method=user_input_binary)
        user_input.set_outputs(outputs="/user_input")

        ifelse = operators.branching.IfElse(self)
        ifelse.set_inputs(flag="/user_input")

        rescale = operators.mask.transformation.Rescale(self, (ifelse, True))
        rescale.set_inputs(mask="/slide/tile/mask_filtered")
        rescale.set_params(rescale_direction=rescale.RESCALE_DIRECTION.TILE_TO_SLIDE)
        rescale.set_outputs(mask="/slide/mask_rescaled")

        upload = operators.image_dx.annotations.Upload(self)
        upload.set_inputs(mask="/slide/mask_rescaled")
        upload.set_params(terms=NUCLEUS)
        upload.set_outputs(ids="/slide/mask_rescaled/ids")

        user_input_wait = operators.debug.ExecuteMethod(self)
        user_input_wait.set_params(method=user_input_unary)

        load = operators.image_dx.annotations.Load(self)
        load.set_inputs(slide="/slide", region="/slide/tile")
        load.set_params(annotation_type=load.ANNOTATION_TYPE.USER, terms=NUCLEUS)
        load.set_outputs(mask="/slide/tile/mask_filtered")

        rescale = operators.mask.transformation.Rescale(self)
        rescale.set_inputs(mask="/slide/tile/mask_filtered")
        rescale.set_params(rescale_direction=rescale.RESCALE_DIRECTION.SLIDE_TO_TILE)
        rescale.set_outputs(mask="/slide/tile/mask_filtered")

        delete = operators.image_dx.annotations.Delete(self)
        delete.set_inputs(slide="/slide")
        delete.set_params(terms=NUCLEUS)

        operators.branching.Join(self, [(ifelse, False), delete])

        self.display_segmentation(all=False)


    def save_result(self):
        execute_method = operators.debug.ExecuteMethod(self)
        execute_method.set_inputs(args=("/slide/tile/mask_filtered", "/slide/tile"))
        execute_method.set_params(method=new_filename)
