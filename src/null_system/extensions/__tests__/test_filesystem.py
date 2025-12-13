"""Tests for filesystem extension."""

import pytest
import tempfile
import json
import zlib
from pathlib import Path
from unittest.mock import patch, mock_open

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from filesystem import (
    NullFSArchive,
    NullFSManager,
    NullFSFile,
    FileMetadata,
    ArchiveHeader,
    CompressionType,
    EncryptionType,
    create_archive_from_directory,
    extract_archive_to_directory
)


class TestFileMetadata:
    """Test FileMetadata class."""
    
    def test_creation(self):
        """Test creating file metadata."""
        metadata = FileMetadata(
            path="test.txt",
            size=1024,
            compression_type=CompressionType.GZIP,
            encryption_type=EncryptionType.AES_256_GCM
        )
        
        assert metadata.path == "test.txt"
        assert metadata.size == 1024
        assert metadata.compression_type == CompressionType.GZIP
        assert metadata.encryption_type == EncryptionType.AES_256_GCM
        assert metadata.compressed_size == 1024  # Default
        assert metadata.created_at is not None
    
    def test_serialization(self):
        """Test dictionary conversion."""
        metadata = FileMetadata(
            path="test.txt",
            size=1024,
            compression_type=CompressionType.GZIP,
            metadata={"custom": "value"}
        )
        
        data = metadata.to_dict()
        assert data["path"] == "test.txt"
        assert data["size"] == 1024
        assert data["compression_type"] == "gzip"
        assert data["metadata"]["custom"] == "value"
        
        restored = FileMetadata.from_dict(data)
        assert restored.path == metadata.path
        assert restored.size == metadata.size
        assert restored.compression_type == metadata.compression_type


class TestArchiveHeader:
    """Test ArchiveHeader class."""
    
    def test_creation(self):
        """Test creating archive header."""
        header = ArchiveHeader(
            version="1.0",
            file_count=10,
            total_size=10240,
            compression_default=CompressionType.GZIP
        )
        
        assert header.version == "1.0"
        assert header.file_count == 10
        assert header.total_size == 10240
        assert header.compression_default == CompressionType.GZIP
        assert header.archive_id is not None
        assert header.created_at is not None
    
    def test_serialization(self):
        """Test dictionary conversion."""
        header = ArchiveHeader(version="2.0", file_count=5)
        
        data = header.to_dict()
        assert data["version"] == "2.0"
        assert data["file_count"] == 5
        assert "created_at" in data
        
        restored = ArchiveHeader.from_dict(data)
        assert restored.version == header.version
        assert restored.file_count == header.file_count


class TestNullFSArchive:
    """Test NullFSArchive class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.archive = NullFSArchive(
            compression_type=CompressionType.GZIP,
            encryption_type=EncryptionType.NONE
        )
    
    def test_creation(self):
        """Test archive creation."""
        assert self.archive.compression_type == CompressionType.GZIP
        assert self.archive.encryption_type == EncryptionType.NONE
        assert len(self.archive.files) == 0
        assert self.archive.archive_header.file_count == 0
    
    def test_add_file_bytes(self):
        """Test adding binary file to archive."""
        content = b"Hello, World!"
        
        self.archive.add_file("test.txt", content)
        
        assert "test.txt" in self.archive.files
        assert self.archive.files["test.txt"].size == len(content)
        assert self.archive.archive_header.file_count == 1
        assert self.archive.archive_header.total_size > 0
    
    def test_add_file_string(self):
        """Test adding string file to archive."""
        content = "Hello, World!"
        
        self.archive.add_file("test.txt", content)
        
        assert "test.txt" in self.archive.files
        stored_content = self.archive.get_file("test.txt")
        assert stored_content == content.encode('utf-8')
    
    def test_compression(self):
        """Test compression functionality."""
        # Add a large, compressible file
        large_content = b"A" * 1000  # Highly compressible
        
        self.archive.add_file("large.txt", large_content)
        
        # Check that compression worked
        file_info = self.archive.files["large.txt"]
        assert file_info.compressed_size < file_info.size
        assert file_info.checksum is not None
        
        # Verify we can decompress and get original content
        retrieved_content = self.archive.get_file("large.txt")
        assert retrieved_content == large_content
    
    def test_get_nonexistent_file(self):
        """Test getting file that doesn't exist."""
        result = self.archive.get_file("nonexistent.txt")
        assert result is None
    
    def test_remove_file(self):
        """Test removing file from archive."""
        self.archive.add_file("test.txt", b"content")
        
        assert "test.txt" in self.archive.files
        
        success = self.archive.remove_file("test.txt")
        assert success == True
        assert "test.txt" not in self.archive.files
        assert self.archive.archive_header.file_count == 0
    
    def test_list_files(self):
        """Test listing files in archive."""
        assert self.archive.list_files() == []
        
        self.archive.add_file("file1.txt", b"content1")
        self.archive.add_file("file2.txt", b"content2")
        
        files = self.archive.list_files()
        assert len(files) == 2
        assert "file1.txt" in files
        assert "file2.txt" in files
    
    def test_get_file_info(self):
        """Test getting file information."""
        self.archive.add_file("test.txt", b"content", metadata={"type": "text"})
        
        info = self.archive.get_file_info("test.txt")
        assert info is not None
        assert info.path == "test.txt"
        assert info.metadata["type"] == "text"
        
        # Test non-existent file
        nonexistent_info = self.archive.get_file_info("nonexistent.txt")
        assert nonexistent_info is None
    
    def test_save_and_load_archive(self):
        """Test saving and loading archive from file."""
        # Add some files
        self.archive.add_file("file1.txt", b"Content 1")
        self.archive.add_file("file2.txt", b"Content 2")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.nfsb') as f:
            temp_path = f.name
        
        try:
            # Save archive
            self.archive.save_to_file(temp_path)
            
            # Load archive in new instance
            loaded_archive = NullFSArchive.load_from_file(temp_path)
            
            # Verify files match
            assert loaded_archive.list_files() == self.archive.list_files()
            
            for filename in self.archive.list_files():
                original_content = self.archive.get_file(filename)
                loaded_content = loaded_archive.get_file(filename)
                assert original_content == loaded_content
                
                original_info = self.archive.get_file_info(filename)
                loaded_info = loaded_archive.get_file_info(filename)
                assert original_info.size == loaded_info.size
        
        finally:
            # Cleanup
            Path(temp_path).unlink(missing_ok=True)
    
    def test_archive_info(self):
        """Test getting archive information."""
        self.archive.add_file("file1.txt", b"A" * 100)  # 100 bytes
        self.archive.add_file("file2.txt", b"B" * 200)  # 200 bytes
        
        info = self.archive.get_archive_info()
        
        assert info["total_files"] == 2
        assert info["total_size"] == 300
        assert "header" in info
        assert "files" in info
        assert len(info["files"]) == 2
    
    def test_pack_directory(self):
        """Test packing directory into archive."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            (temp_path / "file1.txt").write_text("Content 1")
            (temp_path / "subdir").mkdir()
            (temp_path / "subdir" / "file2.txt").write_text("Content 2")
            
            # Pack directory
            self.archive.pack_directory(temp_path)
            
            files = self.archive.list_files()
            assert len(files) >= 2
            assert any("file1.txt" in f for f in files)
            assert any("file2.txt" in f for f in files)
    
    def test_unpack_to_directory(self):
        """Test unpacking archive to directory."""
        # Create archive with some files
        self.archive.add_file("file1.txt", b"Content 1")
        self.archive.add_file("subdir/file2.txt", b"Content 2")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Unpack to directory
            self.archive.unpack_to_directory(temp_path)
            
            # Verify files exist
            assert (temp_path / "file1.txt").exists()
            assert (temp_path / "subdir" / "file2.txt").exists()
            
            # Verify content
            assert (temp_path / "file1.txt").read_bytes() == b"Content 1"
            assert (temp_path / "subdir" / "file2.txt").read_bytes() == b"Content 2"


class TestNullFSManager:
    """Test NullFSManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = NullFSManager()
    
    def test_initialization(self):
        """Test manager initialization."""
        assert len(self.manager.mounts) == 0
        assert len(self.manager.remote_mounts) == 0
    
    def test_create_archive(self):
        """Test creating new archive."""
        archive = self.manager.create_archive(
            "test",
            CompressionType.GZIP,
            EncryptionType.NONE
        )
        
        assert isinstance(archive, NullFSArchive)
        assert "test" in self.manager.mounts
    
    def test_get_archive(self):
        """Test getting archive by name."""
        # Create and mount archive
        archive = self.manager.create_archive("test")
        
        retrieved = self.manager.get_archive("test")
        assert retrieved == archive
        
        # Test non-existent archive
        nonexistent = self.manager.get_archive("nonexistent")
        assert nonexistent is None
    
    def test_list_archives(self):
        """Test listing archives."""
        assert self.manager.list_archives() == []
        
        self.manager.create_archive("archive1")
        self.manager.create_archive("archive2")
        
        archives = self.manager.list_archives()
        assert len(archives) == 2
        assert "archive1" in archives
        assert "archive2" in archives
    
    def test_mount_unmount_archive(self):
        """Test mounting and unmounting archives."""
        # Create an archive
        archive = NullFSArchive()
        archive.add_file("test.txt", b"content")
        
        # Mount it
        self.manager.mount_archive("mounted", archive)
        assert "mounted" in self.manager.mounts
        
        # Unmount it
        success = self.manager.unmount_archive("mounted")
        assert success == True
        assert "mounted" not in self.manager.mounts
        
        # Try to unmount non-existent
        success = self.manager.unmount_archive("nonexistent")
        assert success == False
    
    async def test_create_remote_mount(self):
        """Test creating remote mount."""
        success = await self.manager.create_remote_mount(
            "remote1",
            "remote://server/path",
            {"host": "server", "port": 8080}
        )
        
        assert success == True
        assert "remote1" in self.manager.remote_mounts
        mount_info = self.manager.remote_mounts["remote1"]
        assert mount_info["remote_path"] == "remote://server/path"
    
    def test_get_mount_info(self):
        """Test getting mount information."""
        # Create and mount local archive
        archive = NullFSArchive()
        archive.add_file("test.txt", b"content")
        self.manager.mount_archive("local", archive)
        
        # Get local mount info
        local_info = self.manager.get_mount_info("local")
        assert local_info is not None
        assert local_info["type"] == "local"
        assert "archive_info" in local_info
        
        # Test remote mount
        self.manager.remote_mounts["remote"] = {
            "remote_path": "remote://server/path",
            "mounted_at": "2023-01-01T00:00:00"
        }
        
        remote_info = self.manager.get_mount_info("remote")
        assert remote_info is not None
        assert remote_info["type"] == "remote"
        assert "mount_info" in remote_info
    
    def test_list_mounts(self):
        """Test listing all mounts."""
        # No mounts
        mounts = self.manager.list_mounts()
        assert len(mounts) == 0
        
        # Add local mount
        archive = NullFSArchive()
        archive.add_file("test.txt", b"content")
        self.manager.mount_archive("local1", archive)
        
        # Add remote mount
        self.manager.remote_mounts["remote1"] = {
            "remote_path": "remote://server/path",
            "mounted_at": "2023-01-01T00:00:00"
        }
        
        mounts = self.manager.list_mounts()
        assert len(mounts) == 2
        assert "local1" in mounts
        assert "remote1" in mounts
        assert mounts["local1"]["type"] == "local"
        assert mounts["remote1"]["type"] == "remote"


class TestNullFSFile:
    """Test NullFSFile class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.archive = NullFSArchive()
        self.archive.add_file("test.txt", b"Line 1\nLine 2\nLine 3\n")
        self.archive.add_file("binary.bin", b"\x00\x01\x02\x03\x04")
    
    def test_file_reading(self):
        """Test reading from file."""
        with NullFSFile(self.archive, "test.txt", "r") as f:
            content = f.read()
            assert content == b"Line 1\nLine 2\nLine 3\n"
    
    def test_file_read_with_size(self):
        """Test reading specific number of bytes."""
        with NullFSFile(self.archive, "test.txt", "r") as f:
            content = f.read(6)  # Read "Line 1"
            assert content == b"Line 1"
            assert f.tell() == 6
    
    def test_file_readline(self):
        """Test reading lines."""
        with NullFSFile(self.archive, "test.txt", "r") as f:
            line1 = f.readline()
            line2 = f.readline()
            
            assert line1 == b"Line 1\n"
            assert line2 == b"Line 2\n"
    
    def test_file_seek(self):
        """Test seeking in file."""
        with NullFSFile(self.archive, "test.txt", "r") as f:
            # Seek to position 6
            pos = f.seek(6)
            assert pos == 6
            
            content = f.read(6)  # Should read "Line 2"
            assert content == b"Line 2"
            
            # Seek from current position
            pos = f.seek(2, 1)  # Seek 2 bytes forward
            content = f.read(6)
            assert content == b"ne 3\n"
    
    def test_file_tell(self):
        """Test getting current position."""
        with NullFSFile(self.archive, "test.txt", "r") as f:
            assert f.tell() == 0
            
            f.read(5)
            assert f.tell() == 5
    
    def test_file_not_found(self):
        """Test accessing non-existent file."""
        with pytest.raises(FileNotFoundError):
            with NullFSFile(self.archive, "nonexistent.txt", "r") as f:
                pass
    
    def test_context_manager(self):
        """Test context manager functionality."""
        f = NullFSFile(self.archive, "test.txt", "r")
        
        # File should not be opened yet
        assert f._content is None
        
        with f:
            # Content should be available in context
            assert f._content is not None
            content = f.read()
            assert content == b"Line 1\nLine 2\nLine 3\n"
        
        # Content should be cleared after context
        assert f._content is None
    
    def test_binary_file(self):
        """Test reading binary files."""
        with NullFSFile(self.archive, "binary.bin", "rb") as f:
            content = f.read()
            assert content == b"\x00\x01\x02\x03\x04"


class TestHelperFunctions:
    """Test helper functions for CLI integration."""
    
    def test_create_archive_from_directory(self):
        """Test creating archive from directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            (temp_path / "file1.txt").write_text("Content 1")
            (temp_path / "subdir").mkdir()
            (temp_path / "subdir" / "file2.txt").write_text("Content 2")
            
            # Create archive
            with tempfile.NamedTemporaryFile(delete=False, suffix='.nfsb') as f:
                output_path = f.name
            
            try:
                create_archive_from_directory(temp_path, output_path)
                
                # Verify archive was created
                assert Path(output_path).exists()
                
                # Load and verify
                archive = NullFSArchive.load_from_file(output_path)
                files = archive.list_files()
                assert len(files) >= 2
                
            finally:
                Path(output_path).unlink(missing_ok=True)
    
    def test_extract_archive_to_directory(self):
        """Test extracting archive to directory."""
        # Create archive
        archive = NullFSArchive()
        archive.add_file("file1.txt", b"Content 1")
        archive.add_file("dir/file2.txt", b"Content 2")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.nfsb') as f:
            archive_path = f.name
        
        try:
            # Save archive
            archive.save_to_file(archive_path)
            
            # Extract to directory
            with tempfile.TemporaryDirectory() as temp_dir:
                extract_archive_to_directory(archive_path, temp_dir)
                
                # Verify files exist
                assert (Path(temp_dir) / "file1.txt").exists()
                assert (Path(temp_dir) / "dir" / "file2.txt").exists()
                
                # Verify content
                content1 = (Path(temp_dir) / "file1.txt").read_bytes()
                content2 = (Path(temp_dir) / "dir" / "file2.txt").read_bytes()
                
                assert content1 == b"Content 1"
                assert content2 == b"Content 2"
        
        finally:
            Path(archive_path).unlink(missing_ok=True)


class TestIntegration:
    """Integration tests for filesystem system."""
    
    def test_complete_archive_workflow(self):
        """Test complete archive creation and extraction workflow."""
        # Create archive
        archive = NullFSArchive(compression_type=CompressionType.GZIP)
        
        # Add various types of files
        archive.add_file("text.txt", "Hello, World!")
        archive.add_file("data.json", json.dumps({"key": "value"}))
        archive.add_file("binary.dat", b"\x00\x01\x02\x03\x04")
        
        # Save archive
        with tempfile.NamedTemporaryFile(delete=False, suffix='.nfsb') as f:
            archive_path = f.name
        
        try:
            archive.save_to_file(archive_path)
            
            # Load archive
            loaded_archive = NullFSArchive.load_from_file(archive_path)
            
            # Verify all files
            assert loaded_archive.get_file("text.txt") == b"Hello, World!"
            assert loaded_archive.get_file("data.json") == json.dumps({"key": "value"}).encode()
            assert loaded_archive.get_file("binary.dat") == b"\x00\x01\x02\x03\x04"
            
            # Verify compression worked
            original_info = archive.get_file_info("text.txt")
            loaded_info = loaded_archive.get_file_info("text.txt")
            assert original_info.compressed_size == loaded_info.compressed_size
        
        finally:
            Path(archive_path).unlink(missing_ok=True)
    
    def test_manager_operations(self):
        """Test NullFSManager operations."""
        manager = NullFSManager()
        
        # Create archive
        archive = manager.create_archive("test", CompressionType.GZIP)
        archive.add_file("test.txt", b"Test content")
        
        # Mount archive
        manager.mount_archive("mounted", archive)
        
        # Verify operations
        assert manager.get_archive("test") is not None
        assert manager.get_mount_info("mounted")["type"] == "local"
        
        # List archives and mounts
        assert "test" in manager.list_archives()
        assert "mounted" in manager.list_mounts()
        
        # Unmount
        assert manager.unmount_archive("mounted") == True
        assert manager.get_mount_info("mounted") is None