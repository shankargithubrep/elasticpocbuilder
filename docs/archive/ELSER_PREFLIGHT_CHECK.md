# ELSER Pre-Flight Check Implementation

## Problem

When indexing datasets with `semantic_text` fields, Elasticsearch requires the ELSER model to be deployed and ready. If the model is still downloading or not deployed, bulk indexing fails with timeout errors:

```
status: 408, error: 'inference_exception'
reason: 'Model download task is currently running. Wait for trained model [.elser_model_2_linux-x86_64] download task to complete then try again'
```

## Solution

Added automatic ELSER pre-flight checks and deployment before indexing.

## Implementation

### 1. ELSER Status Check (`check_elser_deployment()`)

**Location**: `src/services/elasticsearch_indexer.py:487-512`

Checks if ELSER is deployed and ready:

```python
def check_elser_deployment(self) -> Tuple[bool, str]:
    """Check if ELSER model is deployed and ready"""
    # Check inference endpoint
    response = self.client.inference.get(inference_id=".elser-2-elasticsearch")

    # Check model deployment status
    model_stats = self.client.ml.get_trained_models_stats(model_id=".elser_model_2*")

    for model in model_stats['trained_model_stats']:
        state = deployment_stats.get('state', 'not_deployed')

        if state == 'started':
            return True, "ELSER model is deployed and ready"
        elif state == 'starting':
            return False, "ELSER model is starting, please wait..."
        elif state == 'downloading':
            return False, "ELSER model is downloading, please wait..."
```

**States**:
- ✅ `started` - Ready to use
- ⚠️ `starting` - Wait for it
- ⚠️ `downloading` - Wait for it
- ❌ `not_deployed` - Not deployed

### 2. ELSER Deployment (`deploy_elser()`)

**Location**: `src/services/elasticsearch_indexer.py:514-544`

Attempts to deploy ELSER if not already running:

```python
def deploy_elser(self) -> Tuple[bool, str]:
    """Deploy ELSER model if not already deployed"""
    # Check current status first
    is_ready, status_msg = self.check_elser_deployment()
    if is_ready:
        return True, status_msg

    # Try to start deployment
    self.client.ml.start_trained_model_deployment(
        model_id=".elser_model_2_linux-x86_64",
        wait_for="starting"
    )
```

**Behavior**:
- If already deployed → returns success
- If not deployed → starts deployment
- If model doesn't exist → instructs user to deploy via Kibana

### 3. Ensure ELSER Ready (`ensure_elser_ready()`)

**Location**: `src/services/elasticsearch_indexer.py:546-603`

Main pre-flight check that waits for ELSER to be ready:

```python
def ensure_elser_ready(self, progress_callback: Optional[callable] = None) -> Tuple[bool, str]:
    """Ensure ELSER is deployed and ready, wait if necessary"""
    # Check if ready
    is_ready, msg = self.check_elser_deployment()
    if is_ready:
        return True, msg

    # If downloading/starting, wait up to 5 minutes
    if "downloading" in msg.lower() or "starting" in msg.lower():
        max_wait = 300  # 5 minutes
        wait_interval = 10  # Check every 10 seconds

        while elapsed < max_wait:
            time.sleep(wait_interval)
            is_ready, msg = self.check_elser_deployment()
            if is_ready:
                return True, msg

    # Not deployed, try to deploy it
    success, deploy_msg = self.deploy_elser()
    if not success:
        return False, deploy_msg
```

**Features**:
- Checks if ELSER is ready
- Waits up to 5 minutes if downloading/starting
- Updates progress callback every 10 seconds
- Attempts deployment if not running
- Returns clear error if deployment fails

### 4. Integration into `index_dataset()`

**Location**: `src/services/elasticsearch_indexer.py:231-240`

Automatically runs before indexing if semantic fields are present:

```python
# Analyze DataFrame with LLM-specified semantic fields
mapping_info = FieldMapper.analyze_dataframe(df, semantic_fields)

# Pre-flight check: Ensure ELSER is ready if semantic fields are used
if mapping_info["semantic_fields"]:
    elser_ready, elser_msg = self.ensure_elser_ready(progress_callback)
    if not elser_ready:
        raise ValueError(
            f"Cannot index with semantic_text fields: {elser_msg}\n\n"
            f"Semantic fields specified: {', '.join(mapping_info['semantic_fields'])}\n\n"
            f"Please deploy ELSER through Kibana > Machine Learning > Trained Models, "
            f"or remove semantic fields from your data generator."
        )
```

**Behavior**:
- Only runs if semantic fields are present
- Waits for ELSER to be ready
- Provides clear error message if ELSER can't be deployed
- Shows progress updates during wait

### 5. UI Integration

**Location**: `app.py:722-762`

Added ELSER check buttons in sidebar:

```python
col1, col2 = st.columns(2)

with col1:
    if st.button("Test Connection"):
        # Connection test code

with col2:
    if st.button("Check ELSER"):
        is_ready, message = indexer.check_elser_deployment()

        if is_ready:
            st.success(f"✅ {message}")
        else:
            st.warning(f"⚠️ {message}")

            # Offer to deploy
            if st.button("Deploy ELSER"):
                deploy_success, deploy_msg = indexer.deploy_elser()
```

**Features**:
- Two-column layout: "Test Connection" and "Check ELSER"
- Green success if ELSER ready
- Yellow warning if not ready
- "Deploy ELSER" button appears if not ready

## User Experience

### Successful Flow

1. User clicks "📤 Index" button
2. Progress shows: "Checking ELSER deployment..." (5%)
3. ELSER is ready → continues to indexing
4. Success message shows semantic fields used

### ELSER Downloading Flow

1. User clicks "📤 Index" button
2. Progress shows: "Checking ELSER deployment..." (5%)
3. Detects ELSER is downloading
4. Progress shows: "Waiting for ELSER (10s)..." (10%)
5. Progress shows: "Waiting for ELSER (20s)..." (12%)
6. ...waits up to 5 minutes...
7. ELSER ready → continues to indexing

### ELSER Not Deployed Flow

1. User clicks "📤 Index" button
2. Progress shows: "Checking ELSER deployment..." (5%)
3. ELSER not deployed
4. Progress shows: "Deploying ELSER model..." (10%)
5. Starts deployment
6. Progress shows: "Waiting for ELSER deployment..." (15%)
7. ELSER starts → continues to indexing

### Error Flow (ELSER Can't Deploy)

1. User clicks "📤 Index" button
2. ELSER check fails
3. Error message shows:
```
❌ Indexing error: Cannot index with semantic_text fields: ELSER model not found.
Please deploy ELSER through Kibana ML > Model Management first.

Semantic fields specified: player_behavior_profile

Please deploy ELSER through Kibana > Machine Learning > Trained Models,
or remove semantic fields from your data generator.
```

## Manual ELSER Check

Users can also check ELSER status independently:

1. Click "Check ELSER" button in sidebar
2. See status:
   - ✅ "ELSER model is deployed and ready"
   - ⚠️ "ELSER model is downloading, please wait..."
   - ⚠️ "ELSER model is starting, please wait..."
   - ❌ "ELSER model is not deployed"
3. If not ready, click "Deploy ELSER" button

## Benefits

✅ **Automatic Detection**: No manual ELSER checks needed
✅ **Smart Waiting**: Waits for download/startup automatically
✅ **Auto-Deployment**: Tries to deploy if not running
✅ **Clear Errors**: Tells users exactly what to do
✅ **Progress Updates**: Shows wait time during ELSER readiness check
✅ **No Failed Indexing**: Prevents 408 timeout errors during bulk indexing

## Timeline

**Without Pre-Flight Check**:
- User clicks Index → Indexing starts → 408 errors → User confused

**With Pre-Flight Check**:
- User clicks Index → ELSER check (2s) → Wait if needed (0-300s) → Indexing succeeds

## Configuration

No configuration needed! The pre-flight check:
- Runs automatically when semantic fields are present
- Uses existing Elasticsearch connection
- Checks `.elser-2-elasticsearch` inference endpoint
- Monitors `.elser_model_2_linux-x86_64` model

## Error Messages

### ELSER Downloading
```
⚠️ ELSER model is downloading, please wait...
Waiting for ELSER (120s)...
```

### ELSER Not Found
```
❌ ELSER model not found. Please deploy ELSER through Kibana ML > Model Management first.
```

### Timeout
```
❌ Timeout waiting for ELSER model to be ready
```

## Future Enhancements

1. **Progress Estimation**: Show download percentage if available
2. **Model Selection**: Support different ELSER versions
3. **Resource Allocation**: Configure deployment resources
4. **Status Caching**: Cache ELSER status for 1 minute to reduce API calls
5. **Fallback Mode**: Option to index without semantic_text if ELSER unavailable

## Summary

The ELSER pre-flight check ensures seamless indexing with semantic_text fields by:
1. Checking ELSER status before indexing
2. Waiting for downloads/startup automatically
3. Attempting deployment if needed
4. Providing clear error messages
5. Showing progress updates

Users no longer see 408 timeout errors - they get clear feedback about ELSER status and what to do next.
