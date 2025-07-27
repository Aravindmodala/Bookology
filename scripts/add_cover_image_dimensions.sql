-- Add image dimension columns to Stories table for proper image display
-- This script adds support for storing image dimensions to prevent cropping

-- Add cover_image_width column to store the image width
ALTER TABLE "Stories" 
ADD COLUMN IF NOT EXISTS "cover_image_width" INTEGER;

-- Add cover_image_height column to store the image height  
ALTER TABLE "Stories" 
ADD COLUMN IF NOT EXISTS "cover_image_height" INTEGER;

-- Add cover_aspect_ratio column for quick aspect ratio calculations
ALTER TABLE "Stories" 
ADD COLUMN IF NOT EXISTS "cover_aspect_ratio" DECIMAL(4,2);

-- Add comments for documentation
COMMENT ON COLUMN "Stories"."cover_image_width" IS 'Width of the generated cover image in pixels';
COMMENT ON COLUMN "Stories"."cover_image_height" IS 'Height of the generated cover image in pixels';
COMMENT ON COLUMN "Stories"."cover_aspect_ratio" IS 'Aspect ratio of the cover image (width/height)';

-- Display success message
DO $$
BEGIN
    RAISE NOTICE 'Cover image dimension columns added successfully to Stories table';
END $$; 