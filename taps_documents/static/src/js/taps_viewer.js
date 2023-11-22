odoo.define('taps_documents.custom_viewer', function (require) {
    'use strict';

    document.addEventListener('DOMContentLoaded', function () {
        
        // Function to check if the 'viewerContainer' element is available
        function checkViewerContainer() {
            
            var viewerContainer = document.querySelector("#viewerContainer, .viewerContainer, [data-viewer-container]");
            console.log('viewerContainer:', viewerContainer);
            // var config = getViewerConfiguration();
            // console.log('config.toolbar.download:', config.toolbar);
            // console.log('config.secondaryToolbar.downloadButton:', config.secondaryToolbar);            
            

            if (viewerContainer) {
                // Your custom code here

                // Access the configuration
                var config = getViewerConfiguration();
                console.log('config.toolbar.download:', config.toolbar.download);
                console.log('config.secondaryToolbar.downloadButton:', config.secondaryToolbar.downloadButton);
                // Show/Hide Download Button based on your condition
                if (shouldHideDownloadButton()) {
                    console.log('Hide Download Button')
                    config.toolbar.download.setAttribute('hidden', 'true');
                    config.secondaryToolbar.downloadButton.setAttribute('hidden', 'true');
                }

                // Call the original function if pdfjsWebApp is available
                if (typeof pdfjsWebApp !== 'undefined') {
                    pdfjsWebApp.webViewerLoad(config);
                }

                // Stop checking once the element is available
                clearInterval(checkInterval);
            }
        }
        // Check every 100 milliseconds
        var checkInterval = setInterval(checkViewerContainer, 1000);

        // Function to determine whether to hide the Download Button
        function shouldHideDownloadButton() {
            // Your logic to determine whether to hide the Download Button
            // For example, you might check if the PDF is in preview mode
            // Replace the condition below with your actual logic
            var isInPreviewMode = true;  // Replace this with your logic
        
            // Log the value of isInPreviewMode to the console
            console.log('isInPreviewMode:', isInPreviewMode);
        
            return isInPreviewMode;
        }

        // Function to get the viewer configuration
        function getViewerConfiguration() {
          return {
            appContainer: document.body,
            mainContainer: document.getElementById('viewerContainer'),
            viewerContainer: document.getElementById('viewer'),
            eventBus: null,
            toolbar: {
              container: document.getElementById('toolbarViewer'),
              numPages: document.getElementById('numPages'),
              pageNumber: document.getElementById('pageNumber'),
              scaleSelectContainer: document.getElementById('scaleSelectContainer'),
              scaleSelect: document.getElementById('scaleSelect'),
              customScaleOption: document.getElementById('customScaleOption'),
              previous: document.getElementById('previous'),
              next: document.getElementById('next'),
              zoomIn: document.getElementById('zoomIn'),
              zoomOut: document.getElementById('zoomOut'),
              viewFind: document.getElementById('viewFind'),
              openFile: document.getElementById('openFile'),
              print: document.getElementById('print'),
              presentationModeButton: document.getElementById('presentationMode'),
              download: document.getElementById('download'),
              viewBookmark: document.getElementById('viewBookmark')
            },
            secondaryToolbar: {
              toolbar: document.getElementById('secondaryToolbar'),
              toggleButton: document.getElementById('secondaryToolbarToggle'),
              toolbarButtonContainer: document.getElementById('secondaryToolbarButtonContainer'),
              presentationModeButton: document.getElementById('secondaryPresentationMode'),
              openFileButton: document.getElementById('secondaryOpenFile'),
              printButton: document.getElementById('secondaryPrint'),
              downloadButton: document.getElementById('secondaryDownload'),
              viewBookmarkButton: document.getElementById('secondaryViewBookmark'),
              firstPageButton: document.getElementById('firstPage'),
              lastPageButton: document.getElementById('lastPage'),
              pageRotateCwButton: document.getElementById('pageRotateCw'),
              pageRotateCcwButton: document.getElementById('pageRotateCcw'),
              cursorSelectToolButton: document.getElementById('cursorSelectTool'),
              cursorHandToolButton: document.getElementById('cursorHandTool'),
              scrollVerticalButton: document.getElementById('scrollVertical'),
              scrollHorizontalButton: document.getElementById('scrollHorizontal'),
              scrollWrappedButton: document.getElementById('scrollWrapped'),
              spreadNoneButton: document.getElementById('spreadNone'),
              spreadOddButton: document.getElementById('spreadOdd'),
              spreadEvenButton: document.getElementById('spreadEven'),
              documentPropertiesButton: document.getElementById('documentProperties')
            },
            fullscreen: {
              contextFirstPage: document.getElementById('contextFirstPage'),
              contextLastPage: document.getElementById('contextLastPage'),
              contextPageRotateCw: document.getElementById('contextPageRotateCw'),
              contextPageRotateCcw: document.getElementById('contextPageRotateCcw')
            },
            sidebar: {
              outerContainer: document.getElementById('outerContainer'),
              viewerContainer: document.getElementById('viewerContainer'),
              toggleButton: document.getElementById('sidebarToggle'),
              thumbnailButton: document.getElementById('viewThumbnail'),
              outlineButton: document.getElementById('viewOutline'),
              attachmentsButton: document.getElementById('viewAttachments'),
              thumbnailView: document.getElementById('thumbnailView'),
              outlineView: document.getElementById('outlineView'),
              attachmentsView: document.getElementById('attachmentsView')
            },
            sidebarResizer: {
              outerContainer: document.getElementById('outerContainer'),
              resizer: document.getElementById('sidebarResizer')
            },
            findBar: {
              bar: document.getElementById('findbar'),
              toggleButton: document.getElementById('viewFind'),
              findField: document.getElementById('findInput'),
              highlightAllCheckbox: document.getElementById('findHighlightAll'),
              caseSensitiveCheckbox: document.getElementById('findMatchCase'),
              entireWordCheckbox: document.getElementById('findEntireWord'),
              findMsg: document.getElementById('findMsg'),
              findResultsCount: document.getElementById('findResultsCount'),
              findPreviousButton: document.getElementById('findPrevious'),
              findNextButton: document.getElementById('findNext')
            },
            passwordOverlay: {
              overlayName: 'passwordOverlay',
              container: document.getElementById('passwordOverlay'),
              label: document.getElementById('passwordText'),
              input: document.getElementById('password'),
              submitButton: document.getElementById('passwordSubmit'),
              cancelButton: document.getElementById('passwordCancel')
            },
            documentProperties: {
              overlayName: 'documentPropertiesOverlay',
              container: document.getElementById('documentPropertiesOverlay'),
              closeButton: document.getElementById('documentPropertiesClose'),
              fields: {
                'fileName': document.getElementById('fileNameField'),
                'fileSize': document.getElementById('fileSizeField'),
                'title': document.getElementById('titleField'),
                'author': document.getElementById('authorField'),
                'subject': document.getElementById('subjectField'),
                'keywords': document.getElementById('keywordsField'),
                'creationDate': document.getElementById('creationDateField'),
                'modificationDate': document.getElementById('modificationDateField'),
                'creator': document.getElementById('creatorField'),
                'producer': document.getElementById('producerField'),
                'version': document.getElementById('versionField'),
                'pageCount': document.getElementById('pageCountField'),
                'pageSize': document.getElementById('pageSizeField'),
                'linearized': document.getElementById('linearizedField')
              }
            },
            errorWrapper: {
              container: document.getElementById('errorWrapper'),
              errorMessage: document.getElementById('errorMessage'),
              closeButton: document.getElementById('errorClose'),
              errorMoreInfo: document.getElementById('errorMoreInfo'),
              moreInfoButton: document.getElementById('errorShowMore'),
              lessInfoButton: document.getElementById('errorShowLess')
            },
            printContainer: document.getElementById('printContainer'),
            openFileInputName: 'fileInput',
            debuggerScriptPath: 'web/static/lib/pdfjs/web/debugger.js'
          };
        }
    });
});
