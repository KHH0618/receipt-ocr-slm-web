package com.khh0618.apiserver.dto.request;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class ReceiptUploadCreateRequest {

    private String imageId;
    private String storagePath;
    private String originalFilename;
    private String mimeType; 
    private Long fileSizeBytes;
    private String sha256;
}
