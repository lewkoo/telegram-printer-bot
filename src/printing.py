"""
Printing module for Telegram Print Bot.

This module handles printer setup and file printing using CUPS/IPP protocol.
It provides a reliable printing solution that works with HP Neverstop Laser MFP 1200w
and other IPP-compatible network printers.

The module uses a proven two-step approach:
1. Setup printer with lpadmin using IPP everywhere driver
2. Print files using lpr command with print options

Author: Levko
License: MIT
"""

import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

# Configure module logger
logger = logging.getLogger(__name__)

# MIME type constants for file type detection
# These are used by bot.py to determine how to handle uploaded files
IMAGE_MIMES = {
    "image/jpeg",
    "image/png", 
    "image/gif",
    "image/tiff",
    "image/webp",
}

PDF_MIME = "application/pdf"

OFFICE_MIMES = {
    "application/msword",  # .doc files
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    "application/vnd.ms-excel",  # .xls files
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
    "application/vnd.ms-powerpoint",  # .ppt files
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # .pptx
    "application/rtf",  # Rich Text Format
    "text/plain",  # Plain text files
}


def setup_printer() -> bool:
    """
    Set up the network printer using CUPS lpadmin command.
    
    This function configures a network printer using the IPP (Internet Printing Protocol)
    with the "everywhere" driver, which provides universal compatibility with modern printers.
    
    The setup process:
    1. Gets printer IP from environment variable
    2. Uses lpadmin to add printer with IPP connection
    3. Enables the printer (-E flag)
    4. Uses 'everywhere' driver for maximum compatibility
    
    Environment Variables:
        PRINTER_IP (str): IP address of the network printer
    
    Returns:
        bool: True if printer setup was successful, False otherwise
        
    Raises:
        subprocess.TimeoutExpired: If printer setup takes longer than 30 seconds
        
    Example:
        >>> setup_printer()
        True
        
    Note:
        This approach is confirmed working with HP Neverstop Laser MFP 1200w
        and should work with any IPP-compatible network printer.
    """
    try:
        # Get printer IP from environment, with fallback to default
        printer_ip = os.getenv("PRINTER_IP", None)

        if not printer_ip:
            logger.error("PRINTER_IP environment variable not set")
            return False
        
        # Construct the lpadmin command for printer setup
        # -p: printer name (HP1200w)
        # -E: enable the printer
        # -v: printer URI using IPP protocol
        # -m: driver model (everywhere = universal IPP driver)
        cmd = [
            "lpadmin", 
            "-p", "HP1200w",  # Printer queue name
            "-E",             # Enable printer
            "-v", f"ipp://{printer_ip}/ipp/print",  # IPP URI
            "-m", "everywhere"  # Universal IPP driver
        ]
        
        # Execute the printer setup command with timeout
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            logger.warning("✅ HP1200w printer setup successful")
            return True
        else:
            logger.error(f"Printer setup failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("Printer setup timed out after 30 seconds")
        return False
    except Exception as e:
        logger.error(f"Printer setup error: {e}")
        return False


def print_file(path: Path, printer_name: Optional[str], media: str, duplex: str, fit_to_page: bool) -> None:
    """
    Print a file using the lpr command.
    
    This function sends a file to the printer using the lpr (line printer) command,
    which is the standard UNIX/Linux printing utility. The function uses a simplified
    approach that has been confirmed to work reliably with HP printers.
    
    Args:
        path (Path): Path to the file to be printed
        printer_name (Optional[str]): Name of the printer (currently unused, defaults to HP1200w)
        media (str): Paper size specification (currently unused for compatibility)
        duplex (str): Duplex printing mode (currently unused for compatibility)
        fit_to_page (bool): Whether to fit content to page (currently unused for compatibility)
    
    Raises:
        RuntimeError: If the printing command fails or times out
        subprocess.TimeoutExpired: If printing takes longer than 30 seconds
        
    Note:
        The parameters printer_name, media, duplex, and fit_to_page are kept for
        compatibility with the bot interface but are not currently used in the
        simplified printing approach. The printer is hardcoded to "HP1200w" which
        corresponds to the printer queue set up by setup_printer().
        
        This simplified approach was chosen after testing showed that complex
        print options could cause compatibility issues with certain printer models.
        
    Example:
        >>> from pathlib import Path
        >>> print_file(Path("/tmp/document.pdf"), None, "A4", "one-sided", True)
        # Prints the document to HP1200w printer
    """
    try:
        # Construct the lpr command for printing
        # -P: specify printer name (HP1200w matches the queue from setup_printer)
        cmd = ["lpr", "-P", "HP1200w", str(path)]
        
        logger.info(f"Print command: {' '.join(cmd)}")
        
        # Execute the print command with timeout
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            logger.info("✅ File printed successfully via lpr -P HP1200w")
        else:
            logger.error(f"Print failed: {result.stderr}")
            raise RuntimeError(f"Print command failed: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        logger.error("Print command timed out after 30 seconds")
        raise RuntimeError("Print command timed out")
    except Exception as e:
        logger.error(f"Printing failed: {e}")
        raise RuntimeError(f"Printing failed: {e}")


# Office document conversion functionality
def convert_office_to_pdf(input_path: Path, out_dir: Path) -> Optional[Path]:
    """
    Convert Microsoft Office documents to PDF using LibreOffice.
    
    This function uses LibreOffice in headless mode to convert various Office
    document formats (Word, Excel, PowerPoint) to PDF format for printing.
    LibreOffice provides excellent compatibility with Microsoft Office formats.
    
    Args:
        input_path (Path): Path to the input Office document
        out_dir (Path): Directory where the converted PDF should be saved
        
    Returns:
        Optional[Path]: Path to the converted PDF file if successful, None if failed
        
    Supported Formats:
        - Microsoft Word (.doc, .docx)
        - Microsoft Excel (.xls, .xlsx) 
        - Microsoft PowerPoint (.ppt, .pptx)
        - Rich Text Format (.rtf)
        - Plain Text (.txt)
        
    Environment Requirements:
        - LibreOffice must be installed in the container
        - Sufficient disk space in out_dir for conversion
        - Sufficient memory for large documents (especially spreadsheets)
        
    Raises:
        subprocess.TimeoutExpired: If conversion takes longer than 60 seconds
        
    Example:
        >>> from pathlib import Path
        >>> input_file = Path("/tmp/document.docx")
        >>> output_dir = Path("/tmp")
        >>> pdf_path = convert_office_to_pdf(input_file, output_dir)
        >>> if pdf_path:
        ...     print(f"Converted to: {pdf_path}")
        ... else:
        ...     print("Conversion failed")
        
    Note:
        This function is optional and only used when ENABLE_LIBREOFFICE=1
        is set in the environment. If LibreOffice is not available, the
        function will return None and log a warning.
    """
    # Check if LibreOffice is available in the system
    soffice = shutil.which("libreoffice") or shutil.which("soffice")
    if not soffice:
        logger.warning("LibreOffice not installed; cannot convert: %s", input_path)
        return None
    
    try:
        # Construct LibreOffice conversion command
        # --headless: run without GUI
        # --convert-to pdf: output format
        # --outdir: specify output directory
        result = subprocess.run([
            soffice, 
            "--headless",           # No GUI mode
            "--convert-to", "pdf",  # Convert to PDF format
            "--outdir", str(out_dir),  # Output directory
            str(input_path)         # Input file path
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            # Construct expected PDF output path
            pdf_path = out_dir / f"{input_path.stem}.pdf"
            if pdf_path.exists():
                logger.info(f"✅ Successfully converted {input_path.name} to PDF")
                return pdf_path
            else:
                logger.error(f"PDF file not found after conversion: {pdf_path}")
                return None
        
        logger.error(f"LibreOffice conversion failed: {result.stderr}")
        return None
        
    except subprocess.TimeoutExpired:
        logger.error(f"LibreOffice conversion timed out for: {input_path}")
        return None
    except Exception as e:
        logger.error(f"LibreOffice conversion error: {e}")
        return None
