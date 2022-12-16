from .folder import Folder


class S3Folder(Folder):
    RESOURCE_TYPE = 'folder'
    DEFAULT_FS = 's3'

    def __init__(self, dryrun: bool, **kwargs):
        from s3fs import S3FileSystem
        # s3fs normally caches directory listings, because these lookups can be expensive.
        # Turn off this caching system to force refresh on every access
        S3FileSystem.clear_instance_cache()

        self.s3 = S3FileSystem(anon=False)
        self.s3.invalidate_cache()

        super().__init__(dryrun=dryrun, **kwargs)

    @staticmethod
    def from_config(config: dict, dryrun=True):
        """ Load config values into the object. """
        return S3Folder(**config, dryrun=dryrun)

    @property
    def bucket_name(self):
        """Extract the bucket name from the full fsspec url path"""
        split_url = list(filter(None, self.url.split('/')))
        if split_url:
            return split_url[0]

    def rsync(self):
        # TODO [JL]
        # Use skypilot's implementation
        pass

    def empty_bucket(self):
        for p in self.s3.ls(self.fsspec_url):
            self.s3.rm(p)

    def delete_in_fs(self, *kwargs):
        """ Delete the folder itself. """
        try:
            self.s3.rmdir(self.bucket_name)
        except OSError:
            # If folder isn't empty delete its contents first
            self.empty_bucket()
            self.delete_in_fs()
        except Exception as e:
            raise Exception(f'Failed to delete bucket: {e}')