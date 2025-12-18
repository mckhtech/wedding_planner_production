#!/usr/bin/env python3
"""Automatically map S3 files to templates in order"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import boto3
from app.config import settings
from app.database import SessionLocal
from app.models.template import Template
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def auto_map_templates():
    """Auto-map S3 files to templates"""
    
    # Get S3 files
    s3_client = boto3.client(
        "s3",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )

    try:
        response = s3_client.list_objects_v2(
            Bucket=settings.S3_BUCKET_NAME,
            Prefix="template_previews/",
        )

        if "Contents" not in response:
            logger.error("❌ No files found in S3")
            return

        # Build public URLs
        s3_files = []
        for obj in response["Contents"]:
            key = obj["Key"]
            if key != "template_previews/":
                url = (
                    f"https://{settings.S3_BUCKET_NAME}.s3."
                    f"{settings.AWS_REGION}.amazonaws.com/{key}"
                )
                s3_files.append(url)

        s3_files.sort()
        logger.info(f"📁 Found {len(s3_files)} files in S3")

        # DB
        db = SessionLocal()
        templates = (
            db.query(Template)
            .order_by(Template.id)
            .limit(len(s3_files))
            .all()
        )

        logger.info(f"🗄️  Found {len(templates)} templates in database\n")

        # Map S3 → templates
        for i, template in enumerate(templates):
            if i < len(s3_files):
                old_url = template.preview_image
                new_url = s3_files[i]

                template.preview_image = new_url

                logger.info(f"✅ Template {template.id}: {template.name}")
                logger.info(f"   OLD: {old_url}")
                logger.info(f"   NEW: {new_url}\n")
            else:
                logger.warning(f"⚠️  No S3 file for Template {template.id}")

        db.commit()
        logger.info("✅ Database updated!")

        # Optional URL test
        print("\n" + "=" * 80)
        print("🔍 Testing URLs:")
        print("=" * 80)

        import requests

        for t in templates:
            if t.preview_image:
                try:
                    r = requests.head(t.preview_image, timeout=5)
                    status = "✅" if r.status_code == 200 else f"❌ {r.status_code}"
                except Exception as e:
                    status = f"❌ {str(e)[:30]}"
                print(f"{status} Template {t.id}: {t.preview_image}")

        db.close()

    except Exception as e:
        logger.error(f"❌ Error: {e}")

if __name__ == "__main__":
    auto_map_templates()
