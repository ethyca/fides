# Access Package Streaming Zip Implementation Plan

## Quick Implementation Summary

### Files to Create (New)
- src/fides/api/service/storage/streaming_zip_service.py - Core streaming service
- src/fides/api/service/storage/s3_streaming.py - S3 streaming adapter
- src/fides/api/service/storage/gcs_streaming.py - GCS streaming adapter
- src/fides/api/service/storage/streaming_response.py - Response header management

### Files to Modify (Existing)
- src/fides/api/api/v1/endpoints/privacy_request_endpoints.py - Add streaming endpoint
- src/fides/api/service/privacy_request/request_runner_service.py - Update attachment handling and storage logic
- src/fides/api/service/privacy_request/attachment_handling.py - Modify attachment processing for streaming
- src/fides/api/service/privacy_request/dsr_package/dsr_report_builder.py - Update to handle streaming vs. presigned URLs
- src/fides/api/tasks/storage.py - Update storage upload logic for streaming
- src/fides/api/service/messaging/message_dispatch_service.py - Update email templates for streaming downloads
- src/fides/api/email_templates/templates/privacy_request_complete_access.html - Update email template for streaming
- src/fides/api/models/messaging_template.py - Update default messaging templates
- clients/admin-ui/src/features/privacy-requests/hooks/useDownloadPrivacyRequestResults.ts - Update download logic
- clients/admin-ui/src/features/privacy-requests/attachments/CustomUploadItem.tsx - Update attachment handling
- clients/admin-ui/src/features/privacy-requests/attachments/privacy-request-attachments.slice.ts - Update API slice for streaming

### Files to Test
- All new streaming services
- Updated API endpoints
- Frontend download functionality
- Integration with existing attachment system

**Timeline**: 3-4 weeks | **Effort**: 21-30 days

**Total Files**: 15 (4 new + 11 modified)

---

## Executive Summary

We want to replace the current presigned link approach for access package attachments with on-demand streaming zip downloads. Right now, we generate presigned URLs for each attachment and include them in the access package. The new approach will stream a zip file containing all attachments directly to the client without loading the entire zip into memory or writing it to disk first.

## Current Implementation Analysis

### Current Flow
1. **Attachment Processing**: get_attachments_content() in attachment_handling.py retrieves attachment metadata and generates presigned URLs
2. **Access Package Generation**: DsrReportBuilder.generate() creates HTML reports and zips them with attachment metadata
3. **Storage Upload**: upload_access_results() uploads the complete access package to S3/GCS
4. **Download**: Users receive presigned URLs to download the access package

### Current Pain Points
- **Memory Usage**: Entire access package gets loaded into memory during generation (except attachments which are just expiring presigned URLs)
- **Storage Overhead**: We're storing complete packages in cloud storage
- **Presigned URL Expiration**: 7-day expiration means we have to regenerate links
- **Scalability**: Large datasets can cause OOM issues

## Proposed Solution: Streaming Zip Downloads

### Implementation Options

We have three main approaches to implement streaming zip downloads, each with different trade-offs:

#### Option 1: API-Based Streaming (Current Plan)
**High-Level Architecture**:
```
Client Request → Our API → Streaming Service → Cloud Storage → Streamed Zip Response
```

**Pros**:
- Full control over the streaming process
- Easier to implement authentication and validation
- Can handle complex business logic
- Consistent with existing API patterns

**Cons**:
- API server load during downloads
- Network latency through our servers
- More complex error handling

#### Option 2: Lambda@Edge + CloudFront (AWS)
**High-Level Architecture**:
```
Client Request → CloudFront → Lambda@Edge → S3 → Streamed Zip Response
```

**Pros**:
- No API server load
- Global CDN distribution for fast downloads
- Serverless scaling
- Lower latency for users

**Cons**:
- AWS-specific implementation
- More complex deployment and monitoring
- Lambda@Edge limitations (5MB payload, 50MB response)

#### Option 3: Cloud Functions (GCP/AWS)
**High-Level Architecture**:
```
Client Request → Cloud Function → Cloud Storage → Streamed Zip Response
```

**Pros**:
- No API server load
- Serverless scaling
- Can handle larger files than Lambda@Edge
- Platform-agnostic (works with GCP or AWS)

**Cons**:
- More complex authentication handling
- Additional service to monitor
- Cold start latency

### Why Streaming Is Better Than Current Approach
- **Memory Efficient**: No more loading entire zip files into memory
- **Ephemeral Storage Friendly**: No temporary files written to disk (great for containers/serverless)
- **Real-time Streaming**: Client gets data while we're still fetching from cloud storage
- **Scalable**: Can handle GB-sized datasets without OOM issues
- **Operationally Efficient**: Eliminates memory pressure and OOM risks from large package generation

## Technical Implementation Plan

### Implementation Approach Selection

Before diving into the technical details, you'll need to choose which streaming approach fits your infrastructure and requirements:

#### **Option 1: API-Based Streaming** (Recommended for Most Teams)
- **Best for**: Teams that want full control and fastest implementation
- **Infrastructure**: Uses existing API servers
- **Complexity**: Low to medium
- **Performance**: Good, with some API server load

#### **Option 2: Lambda@Edge + CloudFront** (AWS-Only)
- **Best for**: AWS-heavy teams that want maximum performance
- **Infrastructure**: Requires CloudFront + Lambda@Edge setup
- **Complexity**: Medium to high
- **Performance**: Excellent, global CDN distribution

#### **Option 3: Cloud Functions** (Platform Agnostic)
- **Best for**: Teams that want serverless without vendor lock-in
- **Infrastructure**: GCP Cloud Functions or AWS Lambda
- **Complexity**: Medium
- **Performance**: Very good, no API server load

### Core Implementation (High Priority)

#### 1.1 Create Streaming Zip Service
**File**: src/fides/api/service/storage/streaming_zip_service.py

**What it does**:
- Creates zip files on-the-fly without loading everything into memory
- Handles S3, GCS, and local storage backends
- Manages the streaming response generation

**Pseudocode**:
```python
class StreamingZipService:
    def create_streaming_zip(
        self,
        attachments: List[AttachmentData],
        privacy_request: PrivacyRequest
    ) -> StreamingResponse:
        # Initialize zip stream
        # Stream each attachment from cloud storage
        # Return streaming response with proper headers
```

#### 1.2 Update Core Attachment Processing
**File**: src/fides/api/service/privacy_request/attachment_handling.py

**Current behavior**: get_attachments_content() generates presigned URLs for each attachment
**What we need to change**: Support streaming attachment content directly instead of just generating URLs
**Why it matters**: This determines how attachments get processed and made available

**Key changes**:
```python
def get_attachments_content(
    loaded_attachments: List[Attachment],
    streaming_mode: bool = False  # New parameter
) -> Iterator[AttachmentData]:
    # If streaming_mode: return attachment metadata for streaming
    # If not streaming_mode: return presigned URLs (existing behavior)
```

#### 1.3 Update Access Results Processing
**File**: src/fides/api/service/privacy_request/request_runner_service.py

**Current behavior**: upload_access_results() always uploads complete access packages to storage
**What we need to change**: Support streaming downloads instead of always uploading to storage
**Why it matters**: This is the core logic for how access results get handled and stored

**Key changes**:
```python
def upload_access_results(
    # ... existing parameters ...
    streaming_enabled: bool = False  # New parameter
) -> list[str]:
    # If streaming_enabled: return streaming endpoint URLs
    # If not streaming_enabled: upload to storage (existing behavior)
```

#### 1.4 Update DSR Report Builder
**File**: src/fides/api/service/privacy_request/dsr_package/dsr_report_builder.py

**Current behavior**: generate() creates HTML reports with attachment metadata and presigned URLs
**What we need to change**: Handle streaming attachments instead of just presigned URL references
**Why it matters**: This determines how the access package structure gets built and what info gets included

**Key changes**:
```python
def generate(self, streaming_mode: bool = False) -> BytesIO:
    # If streaming_mode: include streaming endpoint info instead of presigned URLs
    # If not streaming_mode: include presigned URLs (existing behavior)
```

#### 1.5 Update Storage Upload Logic
**File**: src/fides/api/tasks/storage.py

**Current behavior**: write_to_in_memory_buffer() creates complete packages in memory
**What we need to change**: Support streaming generation instead of always creating in-memory buffers
**Why it matters**: This is the core storage and upload logic for access packages

**Key changes**:
```python
def write_to_in_memory_buffer(
    resp_format: str,
    data: dict[str, Any],
    privacy_request: PrivacyRequest,
    streaming_mode: bool = False  # New parameter
) -> BytesIO:
    # If streaming_mode: return minimal metadata for streaming
    # If not streaming_mode: create complete package (existing behavior)
```

#### 1.6 Implement Cloud Storage Streaming
**Files**:
- src/fides/api/service/storage/s3_streaming.py
- src/fides/api/service/storage/gcs_streaming.py

**What they do**:
- Stream individual files from S3/GCS without downloading to memory
- Handle authentication and error cases
- Provide consistent streaming interface across backends

**Pseudocode**:
```python
class S3StreamingService:
    def stream_file(self, bucket: str, key: str) -> Iterator[bytes]:
        # Use boto3 streaming download
        # Yield chunks without loading entire file

class GCSStreamingService:
    def stream_file(self, bucket: str, blob_name: str) -> Iterator[bytes]:
        # Use google-cloud-storage streaming download
        # Yield chunks without loading entire file
```

#### 1.7 Add Streaming Download Endpoint
**File**: src/fides/api/api/v1/endpoints/privacy_request_endpoints.py

**New endpoint**: GET /api/v1/privacy-request/{privacy_request_id}/access-package/stream

**What it does**:
- Authenticates user and verifies permissions
- Validates privacy request status
- Streams access package zip directly to client

**Pseudocode**:
```python
@router.get("/{privacy_request_id}/access-package/stream")
async def stream_access_package(
    privacy_request_id: str,
    db: Session = Depends(deps.get_db),
    current_user: FidesUser = Depends(deps.get_current_user)
) -> StreamingResponse:
    # Validate request
    # Get attachments
    # Return streaming zip response
```

#### 1.8 Handle Streaming Response Details
**File**: src/fides/api/service/storage/streaming_response.py

**What it does**:
- Generates proper HTTP streaming response headers
- Handles zip file streaming with correct MIME types (`application/zip`)
- Manages content disposition for downloads (`attachment; filename="access_package.zip"`)
- Sets appropriate cache headers and streaming optimizations
- Handles CORS headers for cross-origin requests

**Key headers we need to set**:
```python
headers = {
    "Content-Type": "application/zip",
    "Content-Disposition": f'attachment; filename="access_package_{request_id}.zip"',
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0"
}
```

### Frontend Integration (Medium Priority)

#### 2.1 Update Admin UI
**File**: clients/admin-ui/src/features/privacy-requests/hooks/useDownloadPrivacyRequestResults.ts

**What we need to change**:
- Add streaming download option alongside existing presigned URL download
- Implement streaming download handler
- Update UI to show streaming availability

#### 2.2 Update Attachment Components
**File**: clients/admin-ui/src/features/privacy-requests/attachments/CustomUploadItem.tsx

**What we need to change**:
- Modify download logic to use streaming when available
- Update attachment display to indicate streaming support
- Handle streaming download errors gracefully

#### 2.3 Update API Slice
**File**: clients/admin-ui/src/features/privacy-requests/attachments/privacy-request-attachments.slice.ts

**What we need to change**:
- Add new API endpoint for streaming downloads
- Update attachment queries to support streaming mode
- Handle streaming download responses

### Messaging System Updates (Medium Priority)

#### 2.4 Update Email Templates
**File**: src/fides/api/email_templates/templates/privacy_request_complete_access.html

**Current behavior**: Email contains presigned URL download links
**What we need to change**: Support streaming download endpoints
**Why it matters**: This affects how users get notified about completed access requests

**Key changes**:
```html
<!-- If streaming enabled: -->
<p>Your data access has been completed. Click the link below to download your data:</p>
<a href="{{streaming_download_url}}">Download Access Package</a>

<!-- If not streaming: existing presigned URL logic -->
```

#### 2.5 Update Messaging Service
**File**: src/fides/api/service/messaging/message_dispatch_service.py

**Current behavior**: _build_email() and _build_sms() handle presigned URL links
**What we need to change**: Support streaming download URLs in notifications
**Why it matters**: This affects how completion messages get sent to users

**Key changes**:
```python
def _build_email(
    # ... existing parameters ...
    streaming_enabled: bool = False  # New parameter
) -> EmailForActionType:
    # If streaming_enabled: use streaming endpoint URLs
    # If not streaming_enabled: use presigned URLs (existing behavior)
```

#### 2.6 Update Messaging Templates
**File**: src/fides/api/models/messaging_template.py

**Current behavior**: DEFAULT_MESSAGING_TEMPLATES contain presigned URL references
**What we need to change**: Support streaming download URLs in template variables
**Why it matters**: This affects default email and SMS message content

## Implementation Details

### Streaming Zip Creation Strategy

#### Approach 1: Python zipfile with StreamingResponse
```python
# Use zipfile.ZipFile with BytesIO for each file
# Stream zip structure while streaming file contents
# Maintain zip integrity during streaming
```

#### Approach 2: Custom Zip Streaming
```python
# Implement custom zip streaming without zipfile module
# Direct control over zip format and streaming
# Better memory management but more complex
```

**Recommendation**: Start with Approach 1 for faster implementation, migrate to Approach 2 if we need better memory management

### Cloud Storage Integration

#### S3 Streaming
- Use `boto3.s3.transfer.TransferConfig` for chunked downloads
- Implement `get_object()` with streaming response
- Handle multipart downloads for large files
- **Important**: Use `TransferConfig(max_io_chunk_size=8192)` for optimal streaming performance
- Handle S3-specific errors (NoSuchKey, AccessDenied, etc.) gracefully

#### GCS Streaming
- Use `google.cloud.storage.Blob.download_to_file()` with streaming
- Implement chunked download with `download_to_file()`
- Handle authentication and retry logic
- **Important**: Use `download_as_file()` with file-like objects for streaming
- Handle GCS-specific errors (NotFound, Forbidden, etc.) gracefully

#### Local Storage Streaming
- Implement file streaming for local storage backend
- Use `open(file_path, 'rb')` with chunked reading
- Handle file permission and existence errors
- **Important**: Make sure we clean up file handles to prevent resource leaks

### Error Handling and Edge Cases

#### Network Failures
- Implement retry logic for cloud storage operations
- Handle partial downloads gracefully
- Provide meaningful error messages to users
- Implement circuit breaker pattern for repeated failures

#### Large File Handling
- Implement chunked streaming for files >100MB
- Add progress tracking for long-running downloads
- Handle timeout scenarios appropriately
- Monitor memory usage during streaming to prevent OOM

#### Authentication Issues
- Validate user permissions before streaming
- Handle expired credentials gracefully
- Implement proper security headers
- Validate privacy request status before allowing streaming

#### Streaming-Specific Gotchas
- **Zip File Integrity**: Make sure zip file structure stays valid even if streaming fails mid-way
- **Content Length**: Can't set Content-Length header for streaming responses
- **Partial Downloads**: Handle client disconnections gracefully without corrupting the zip
- **Memory Leaks**: Make sure we clean up file handles and streaming buffers
- **Concurrent Requests**: Handle multiple simultaneous streaming requests efficiently
- **Browser Compatibility**: Test streaming downloads across different browsers and devices

## Testing Strategy

### Unit Tests
- Test streaming service with mock cloud storage
- Validate zip file integrity
- Test error handling scenarios

### Integration Tests
- Test with real S3/GCS buckets
- Validate streaming performance
- Test with various file sizes and types

### Performance Tests
- Measure memory usage during streaming
- Test concurrent download scenarios
- Validate streaming speed vs. traditional downloads


## Risk Assessment

### Technical Risks
- **Medium**: Streaming complexity might introduce bugs
- **Low**: Cloud storage API changes
- **Medium**: Memory management in streaming scenarios

### Performance Risks
- **Low**: Streaming overhead vs. traditional downloads
- **Medium**: Network latency impact on streaming
- **Low**: Concurrent download handling

### Compatibility Risks
- **Low**: Backward compatibility maintained
- **Medium**: Frontend integration complexity
- **Low**: API contract changes

## Effort Estimation

### Development Effort
- **Core Streaming Service**: 3-4 days
- **Cloud Storage Streaming Adapters**: 2-3 days
- **API Endpoint Updates**: 1 day
- **Frontend Integration**: 2-3 days
- **Testing & Polish**: 3-4 days

**Total Development**: 11-15 days

### Testing Effort
- **Unit Testing**: 2-3 days
- **Integration Testing**: 2-3 days
- **Performance Testing**: 1-2 days
- **End-to-End Testing**: 2-3 days

**Total Testing**: 7-11 days

### Documentation and Deployment
- **Documentation Updates**: 1-2 days
- **Deployment Planning**: 1 day
- **Production Deployment**: 1 day

**Total Additional Effort**: 3-4 days

### Overall Project Timeline
**Total Estimated Effort**: 21-30 days (3-4 weeks)

## Success Metrics

### Performance Metrics
- **Memory Usage**: <100MB peak during streaming (vs. current GB+ usage)
- **Download Speed**: Comparable to presigned URL downloads
- **Scalability**: Support for 100+ attachments per package

### User Experience Metrics
- **Download Success Rate**: >99% successful streaming downloads
- **Error Rate**: <1% streaming failures
- **User Adoption**: >80% of users prefer streaming over presigned URLs

### Operational Metrics
- **Storage Cost Reduction**: 30-50% reduction in cloud storage costs
- **System Reliability**: Better uptime due to reduced memory pressure
- **Maintenance Overhead**: Less operational complexity

## Conclusion

Implementing streaming zip downloads for access package attachments will give us a much more efficient, scalable system. This focused implementation delivers real benefits in memory usage, storage costs, and system reliability.

The 3-4 week timeline is realistic, with the core streaming service being the highest priority. We're leveraging existing FastAPI capabilities and Python libraries to get streaming functionality working efficiently.

This change follows modern cloud-native architecture principles and sets us up for better scalability as attachment volumes grow, all while keeping the development timeline reasonable.

---

## Bare Minimum Implementation (MVP)

If you want to get streaming working with the absolute minimum effort, here are three approaches:

### **Option 1: API-Based Streaming (Simplest, 2-3 days)**
**Core Files (3 files)**:
1. **Create streaming zip service** - `src/fides/api/service/storage/streaming_zip_service.py`
   - Basic zip streaming using Python's zipfile module
   - Only handle S3 for now (skip GCS and local)
   - Minimal error handling

2. **Add streaming endpoint** - `src/fides/api/api/v1/endpoints/privacy_request_endpoints.py`
   - Single new endpoint: `GET /{privacy_request_id}/access-package/stream`
   - Basic auth and validation
   - Call the streaming service

3. **Update attachment handling** - `src/fides/api/service/privacy_request/attachment_handling.py`
   - Add streaming_mode parameter to get_attachments_content()
   - Skip presigned URL generation when streaming

**MVP Result**: Users can stream download access packages via API, memory usage drops from GB to <100MB

### **Option 2: Lambda@Edge + CloudFront (AWS Only, 3-4 days)**
**Core Files (2 files)**:
1. **Create Lambda@Edge function** - `lambda/streaming_zip_function.py`
   - Handle zip creation and streaming from S3
   - Basic authentication validation
   - CloudFront integration

2. **Update CloudFront configuration** - `infrastructure/cloudfront.yml`
   - Route streaming requests to Lambda@Edge
   - Handle CORS and security headers

**MVP Result**: Direct streaming from CloudFront, no API load, global CDN distribution

### **Option 3: Cloud Functions (Platform Agnostic, 3-4 days)**
**Core Files (2 files)**:
1. **Create cloud function** - `functions/streaming_zip_function.py`
   - Handle zip creation and streaming
   - Authentication and validation
   - Platform-specific deployment configs

2. **Update deployment scripts** - `scripts/deploy_functions.py`
   - Deploy to GCP Cloud Functions or AWS Lambda
   - Handle environment configuration

**MVP Result**: Serverless streaming without API load, works with any cloud provider

### **What You Can Skip (for now):**
- Frontend updates (users can hit the API/function directly)
- Messaging system updates (keep existing email templates)
- DSR report builder changes (streaming bypasses this)
- Storage upload logic changes (streaming doesn't use it)
- GCS and local storage support (for API approach)
- Comprehensive error handling
- Progress tracking
- Browser compatibility testing

### **MVP Recommendation:**
- **Start with Option 1** (API-based) if you want the fastest implementation
- **Choose Option 2** if you're AWS-only and want the best performance
- **Choose Option 3** if you want platform flexibility and no API load

**Bottom line**: You can get 80% of the benefit with 20% of the work by focusing on just the core streaming service.
