# Save all registered slides as ome.tiff
registrar.warp_and_save_slides(registered_slide_dst_dir, crop="overlap")

# Kill the JVM
registration.kill_jvm()
print("Conversion complete!")
