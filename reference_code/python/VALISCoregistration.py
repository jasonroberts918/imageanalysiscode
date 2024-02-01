# Align each image to a reference image and perform micro-registration
from valis import registration
slide_src_dir = "/Users/User/Downloads/Images for VALIS Coregistration"
results_dst_dir = "/Users/User/Downloads/VALIS Coregistered"
registered_slide_dst_dir = "/Users/User/Downloads/VALIS Coregistered/Slides"
reference_slide = "image.svs"

# Create a Valis object and use it to register the slides in slide_src_dir, aligning *towards* the reference slide.
registrar = registration.Valis(slide_src_dir, results_dst_dir, reference_img_f=reference_slide)
rigid_registrar, non_rigid_registrar, error_df = registrar.register()

# Perform micro-registration on higher resolution images, aligning *directly to* the reference image
registrar.register_micro(max_non_rigid_registration_dim_px=2000, align_to_reference=True)
print("Coregistration complete!")
