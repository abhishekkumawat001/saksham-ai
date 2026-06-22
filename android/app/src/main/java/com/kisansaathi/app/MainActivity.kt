package com.kisansaathi.app

import android.annotation.SuppressLint
import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.net.http.SslError
import android.os.Bundle
import android.view.View
import android.webkit.*
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private lateinit var swipeRefresh: SwipeRefreshLayout

    // Holds the callback for the file chooser so onActivityResult can resolve it
    private var fileChooserCallback: ValueCallback<Array<Uri>>? = null

    companion object {
        private const val APP_URL = "https://saksham-ai.onrender.com"

        private const val FILE_CHOOSER_CODE = 1001
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        swipeRefresh = findViewById(R.id.swipeRefresh)
        webView      = findViewById(R.id.webview)

        configureWebView()
        setupSwipeRefresh()

        // Restore scroll position / page across rotation without reloading
        if (savedInstanceState != null) {
            webView.restoreState(savedInstanceState)
        } else {
            webView.loadUrl(APP_URL)
        }
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun configureWebView() {
        webView.settings.apply {
            javaScriptEnabled      = true   // React requires JS
            domStorageEnabled      = true   // zustand persists to localStorage
            allowFileAccess        = true   // needed for file:// uploads in diagnose
            allowContentAccess     = true
            setSupportZoom(false)           // disable pinch-zoom; Tailwind handles sizing
            builtInZoomControls    = false
            displayZoomControls    = false
            useWideViewPort        = true
            loadWithOverviewMode   = true
            mediaPlaybackRequiresUserGesture = false
            mixedContentMode       = WebSettings.MIXED_CONTENT_NEVER_ALLOW
        }

        webView.webViewClient = KisanWebViewClient()
        webView.webChromeClient = KisanWebChromeClient()
    }

    private fun setupSwipeRefresh() {
        swipeRefresh.setColorSchemeColors(getColor(R.color.brand_green))
        swipeRefresh.setOnRefreshListener {
            webView.reload()
        }
    }

    // -----------------------------------------------------------------------
    // WebViewClient — handles navigation and error states
    // -----------------------------------------------------------------------
    private inner class KisanWebViewClient : WebViewClient() {

        override fun onPageFinished(view: WebView, url: String) {
            swipeRefresh.isRefreshing = false
        }

        override fun onReceivedError(
            view: WebView,
            request: WebResourceRequest,
            error: WebResourceError,
        ) {
            // Only show the dialog for the main frame (not sub-resource failures)
            if (request.isForMainFrame) {
                swipeRefresh.isRefreshing = false
                showNetworkError()
            }
        }

        override fun onReceivedSslError(
            view: WebView,
            handler: SslErrorHandler,
            error: SslError,
        ) {
            // Never proceed on SSL errors — cancel and warn the user.
            handler.cancel()
            AlertDialog.Builder(this@MainActivity)
                .setTitle("Security Warning")
                .setMessage("The connection is not secure. Please contact support.")
                .setPositiveButton("OK", null)
                .show()
        }

        // Keep React Router links inside the WebView instead of opening the browser
        override fun shouldOverrideUrlLoading(
            view: WebView,
            request: WebResourceRequest,
        ): Boolean {
            val url = request.url.toString()
            return when {
                url.startsWith(APP_URL) -> false   // stay in WebView
                url.startsWith("http")  -> {
                    // External link → open in system browser
                    startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
                    true
                }
                else -> false
            }
        }
    }

    // -----------------------------------------------------------------------
    // WebChromeClient — handles JS permissions, file chooser, and progress
    // -----------------------------------------------------------------------
    private inner class KisanWebChromeClient : WebChromeClient() {

        override fun onProgressChanged(view: WebView, newProgress: Int) {
            swipeRefresh.isRefreshing = newProgress < 100
        }

        // Grant camera / microphone when the page asks (diagnose + voice features)
        override fun onPermissionRequest(request: PermissionRequest) {
            request.grant(request.resources)
        }

        // Forward file chooser intents to Android so react-dropzone works
        override fun onShowFileChooser(
            view: WebView,
            filePath: ValueCallback<Array<Uri>>,
            params: FileChooserParams,
        ): Boolean {
            // Cancel any previous pending callback first
            fileChooserCallback?.onReceiveValue(null)
            fileChooserCallback = filePath

            val intent = params.createIntent()
            return try {
                startActivityForResult(intent, FILE_CHOOSER_CODE)
                true
            } catch (e: Exception) {
                fileChooserCallback = null
                false
            }
        }
    }

    // -----------------------------------------------------------------------
    // File chooser result
    // -----------------------------------------------------------------------
    @Deprecated("Deprecated in API 33 but needed for older targets")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        if (requestCode == FILE_CHOOSER_CODE) {
            val results = if (resultCode == Activity.RESULT_OK) {
                WebChromeClient.FileChooserParams.parseResult(resultCode, data)
            } else {
                null
            }
            fileChooserCallback?.onReceiveValue(results)
            fileChooserCallback = null
        }
        super.onActivityResult(requestCode, resultCode, data)
    }

    // -----------------------------------------------------------------------
    // Back button — navigate within the app before exiting
    // -----------------------------------------------------------------------
    @Deprecated("Deprecated in API 33")
    override fun onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack()
        } else {
            super.onBackPressed()
        }
    }

    // -----------------------------------------------------------------------
    // Lifecycle — save/restore WebView state across config changes
    // -----------------------------------------------------------------------
    override fun onSaveInstanceState(outState: Bundle) {
        super.onSaveInstanceState(outState)
        webView.saveState(outState)
    }

    override fun onResume() {
        super.onResume()
        webView.onResume()
    }

    override fun onPause() {
        webView.onPause()
        super.onPause()
    }

    // -----------------------------------------------------------------------
    // Helpers
    // -----------------------------------------------------------------------
    private fun showNetworkError() {
        AlertDialog.Builder(this)
            .setTitle("Connection Error")
            .setMessage(getString(R.string.error_no_internet))
            .setPositiveButton("Retry") { _, _ -> webView.reload() }
            .setNegativeButton("Cancel", null)
            .show()
    }
}