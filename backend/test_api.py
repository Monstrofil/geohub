import asyncio
import aiohttp
import json
import os


async def test_api():
    """Test the API endpoints"""
    base_url = "http://localhost:8000/api/v1"
    
    async with aiohttp.ClientSession() as session:
        # Test health endpoint
        print("Testing health endpoint...")
        async with session.get("http://localhost:8000/health") as response:
            print(f"Health: {response.status} - {await response.text()}")
        
        # Test list files (should be empty)
        print("\nTesting list files...")
        async with session.get(f"{base_url}/files") as response:
            data = await response.json()
            print(f"Files: {response.status} - {len(data['files'])} files found")
        
        # Test file upload (create a test file)
        print("\nTesting file upload...")
        test_file_content = b"This is a test file content"
        
        # Create form data
        data = aiohttp.FormData()
        data.add_field('file', 
                      test_file_content,
                      filename='test.txt',
                      content_type='text/plain')
        
        tags = {"type": "text", "name": "test.txt", "test": "true"}
        data.add_field('tags', json.dumps(tags))
        
        async with session.post(f"{base_url}/files/upload", data=data) as response:
            if response.status == 200:
                file_data = await response.json()
                print(f"Upload: {response.status} - File ID: {file_data['id']}")
                file_id = file_data['id']
            else:
                print(f"Upload failed: {response.status} - {await response.text()}")
                return
        
        # Test get file
        print("\nTesting get file...")
        async with session.get(f"{base_url}/files/{file_id}") as response:
            if response.status == 200:
                file_data = await response.json()
                print(f"Get file: {response.status} - Name: {file_data['original_name']}")
            else:
                print(f"Get file failed: {response.status} - {await response.text()}")
        
        # Test update tags
        print("\nTesting update tags...")
        new_tags = {"type": "text", "name": "test.txt", "updated": "true", "priority": "high"}
        async with session.put(f"{base_url}/files/{file_id}/tags", 
                              json={"tags": new_tags}) as response:
            if response.status == 200:
                tag_data = await response.json()
                print(f"Update tags: {response.status} - Tags: {tag_data['tags']}")
            else:
                print(f"Update tags failed: {response.status} - {await response.text()}")
        
        # Test search files
        print("\nTesting search files...")
        search_data = {"tags": {"type": "text"}}
        async with session.post(f"{base_url}/files/search", json=search_data) as response:
            if response.status == 200:
                search_result = await response.json()
                print(f"Search: {response.status} - Found {len(search_result['files'])} files")
            else:
                print(f"Search failed: {response.status} - {await response.text()}")
        
        # Test list files again (should have our file)
        print("\nTesting list files again...")
        async with session.get(f"{base_url}/files") as response:
            data = await response.json()
            print(f"Files: {response.status} - {len(data['files'])} files found")
        
        # Test delete file
        print("\nTesting delete file...")
        async with session.delete(f"{base_url}/files/{file_id}") as response:
            if response.status == 200:
                print(f"Delete: {response.status} - File deleted successfully")
            else:
                print(f"Delete failed: {response.status} - {await response.text()}")


if __name__ == "__main__":
    asyncio.run(test_api()) 