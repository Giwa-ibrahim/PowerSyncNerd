
from typing import List, Dict
from datetime import datetime


def format_email_html(summaries: List[Dict]) -> str:
    """
    Format summaries as clean, professional HTML email
    Groups by impact level: HIGH → MEDIUM → LOW
    
    Args:
        summaries: List of summary dictionaries from summarizer
    
    Returns:
        HTML string ready for email sending
    """
    # Group by impact
    high = [s for s in summaries if s['impact'] == 'HIGH']
    medium = [s for s in summaries if s['impact'] == 'MEDIUM']
    low = [s for s in summaries if s['impact'] == 'LOW']
    
    current_date = datetime.now().strftime('%B %d, %Y')
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>Nigeria Power Sector Digest</title>
    <!--[if mso]>
    <style type="text/css">
        body, table, td {{ font-family: Arial, Helvetica, sans-serif !important; }}
    </style>
    <![endif]-->
</head>
<body style="margin: 0; padding: 0; background-color: #f3f4f6; font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #f3f4f6;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <!-- Main Container -->
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06); max-width: 800px; margin: 0 auto;">
                    
                    <!-- Header -->
                    <tr>
                        <td style="padding: 50px 40px 40px; text-align: center; border-bottom: 4px solid #1f2937;">
                            <h1 style="margin: 0 0 12px; color: #111827; font-size: 32px; font-weight: 800; line-height: 1.2;">
                                ⚡ Nigeria Power Sector Digest
                            </h1>
                            <p style="margin: 0; color: #4b5563; font-size: 16px; font-weight: 500;">
                                {current_date} • {len(summaries)} Articles
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 50px 40px;">
                            <h2 style="font-size: 24px; color: #2c3e50; margin-top: 0; margin-bottom: 30px; font-weight: 500;">Hello %%SUBSCRIBER_NAME%%,</h2>
"""

    # HIGH IMPACT SECTION
    if high:
        html += """
                            <!-- High Impact Section -->
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="margin-bottom: 40px;">
                                <tr>
                                    <td style="background-color: #e74c3c; color: #ffffff; padding: 12px 20px; border-radius: 6px; font-size: 18px; font-weight: 700; margin-bottom: 20px;">
                                        🔴 High Impact News
                                    </td>
                                </tr>
"""
        for article in high:
            html += f"""
                                <tr>
                                    <td style="padding-top: 20px;">
                                        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #fff9f9; border-left: 4px solid #e74c3c; border-radius: 6px; padding: 20px; margin-bottom: 15px;">
                                            <tr>
                                                <td>
                                                    <h2 style="margin: 0 0 10px; color: #2c3e50; font-size: 18px; font-weight: 700; line-height: 1.4;">
                                                        {article['title']}
                                                    </h2>
                                                    <p style="margin: 0 0 12px; color: #7f8c8d; font-size: 13px; line-height: 1.5;">
                                                        <span style="margin-right: 15px;">📰 {article['source']}</span>
                                                        <span style="margin-right: 15px;">✍️ {article['author']}</span>
                                                        <span>📅 {article['published_date']}</span>
                                                    </p>
                                                    <p style="margin: 0 0 15px; color: #555555; font-size: 15px; line-height: 1.6;">
                                                        {article['summary']}
                                                    </p>
                                                    <a href="{article['url']}" style="display: inline-block; color: #3498db; text-decoration: none; font-weight: 700; font-size: 14px; border-bottom: 2px solid #3498db; padding-bottom: 2px;">
                                                        Read full article →
                                                    </a>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
"""
        html += """
                            </table>
"""

    # MEDIUM IMPACT SECTION
    if medium:
        html += """
                            <!-- Medium Impact Section -->
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="margin-bottom: 40px;">
                                <tr>
                                    <td style="background-color: #f39c12; color: #ffffff; padding: 12px 20px; border-radius: 6px; font-size: 18px; font-weight: 700; margin-bottom: 20px;">
                                        🟠 Medium Impact News
                                    </td>
                                </tr>
"""
        for article in medium:
            html += f"""
                                <tr>
                                    <td style="padding-top: 20px;">
                                        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #fffbf5; border-left: 4px solid #f39c12; border-radius: 6px; padding: 20px; margin-bottom: 15px;">
                                            <tr>
                                                <td>
                                                    <h2 style="margin: 0 0 10px; color: #2c3e50; font-size: 18px; font-weight: 700; line-height: 1.4;">
                                                        {article['title']}
                                                    </h2>
                                                    <p style="margin: 0 0 12px; color: #7f8c8d; font-size: 13px; line-height: 1.5;">
                                                        <span style="margin-right: 15px;">📰 {article['source']}</span>
                                                        <span style="margin-right: 15px;">✍️ {article['author']}</span>
                                                        <span>📅 {article['published_date']}</span>
                                                    </p>
                                                    <p style="margin: 0 0 15px; color: #555555; font-size: 15px; line-height: 1.6;">
                                                        {article['summary']}
                                                    </p>
                                                    <a href="{article['url']}" style="display: inline-block; color: #3498db; text-decoration: none; font-weight: 700; font-size: 14px; border-bottom: 2px solid #3498db; padding-bottom: 2px;">
                                                        Read full article →
                                                    </a>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
"""
        html += """
                            </table>
"""

    # LOW IMPACT SECTION
    if low:
        html += """
                            <!-- Low Impact Section -->
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="margin-bottom: 20px;">
                                <tr>
                                    <td style="background-color: #3498db; color: #ffffff; padding: 12px 20px; border-radius: 6px; font-size: 18px; font-weight: 700; margin-bottom: 20px;">
                                        🔵 Low Impact News
                                    </td>
                                </tr>
"""
        for article in low:
            html += f"""
                                <tr>
                                    <td style="padding-top: 20px;">
                                        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #f5f9fc; border-left: 4px solid #3498db; border-radius: 6px; padding: 20px; margin-bottom: 15px;">
                                            <tr>
                                                <td>
                                                    <h2 style="margin: 0 0 10px; color: #2c3e50; font-size: 18px; font-weight: 700; line-height: 1.4;">
                                                        {article['title']}
                                                    </h2>
                                                    <p style="margin: 0 0 12px; color: #7f8c8d; font-size: 13px; line-height: 1.5;">
                                                        <span style="margin-right: 15px;">📰 {article['source']}</span>
                                                        <span style="margin-right: 15px;">✍️ {article['author']}</span>
                                                        <span>📅 {article['published_date']}</span>
                                                    </p>
                                                    <p style="margin: 0 0 15px; color: #555555; font-size: 15px; line-height: 1.6;">
                                                        {article['summary']}
                                                    </p>
                                                    <a href="{article['url']}" style="display: inline-block; color: #3498db; text-decoration: none; font-weight: 700; font-size: 14px; border-bottom: 2px solid #3498db; padding-bottom: 2px;">
                                                        Read full article →
                                                    </a>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
"""
        html += """
                            </table>
"""

    # Footer
    html += """
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 30px 40px; text-align: center; border-top: 2px solid #ecf0f1; background-color: #fafafa;">
                            <p style="margin: 0 0 5px; color: #2c3e50; font-size: 15px; font-weight: 700;">
                                PowerDigest
                            </p>
                            <p style="margin: 0; color: #7f8c8d; font-size: 13px; line-height: 1.5;">
                                Nigeria Power Sector Intelligence<br>
                                Automated news analysis powered by AI
                            </p>
                             <p style="margin: 20px 0 0; color: #95a5a6; font-size: 11px;">
                                You are receiving this because you subscribed to PowerDigest.<br>
                                <a href="%%UNSUBSCRIBE_URL%%" style="color: #95a5a6; text-decoration: underline;">Unsubscribe</a> from these updates.
                            </p>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    
    return html


def format_plain_text(summaries: List[Dict]) -> str:
    """
    Format summaries as plain text email (fallback)
    
    Args:
        summaries: List of summary dictionaries
    
    Returns:
        Plain text string
    """
    lines = [
        "=" * 80,
        "NIGERIA POWER SECTOR DIGEST",
        "=" * 80,
        f"\nDate: {datetime.now().strftime('%B %d, %Y')}",
        f"Total Articles: {len(summaries)}\n"
    ]
    
    # Group by impact
    high = [s for s in summaries if s['impact'] == 'HIGH']
    medium = [s for s in summaries if s['impact'] == 'MEDIUM']
    low = [s for s in summaries if s['impact'] == 'LOW']
    
    # HIGH IMPACT
    if high:
        lines.append("\n" + "=" * 80)
        lines.append("HIGH IMPACT NEWS")
        lines.append("=" * 80)
        for article in high:
            lines.append(f"\n{article['title']}")
            lines.append(f"Source: {article['source']} | Author: {article['author']} | Date: {article['published_date']}")
            lines.append(f"\n{article['summary']}")
            lines.append(f"\nRead more: {article['url']}\n")
    
    # MEDIUM IMPACT
    if medium:
        lines.append("\n" + "=" * 80)
        lines.append("MEDIUM IMPACT NEWS")
        lines.append("=" * 80)
        for article in medium:
            lines.append(f"\n{article['title']}")
            lines.append(f"Source: {article['source']} | Author: {article['author']} | Date: {article['published_date']}")
            lines.append(f"\n{article['summary']}")
            lines.append(f"\nRead more: {article['url']}\n")
    
    # LOW IMPACT
    if low:
        lines.append("\n" + "=" * 80)
        lines.append("LOW IMPACT NEWS")
        lines.append("=" * 80)
        for article in low:
            lines.append(f"\n{article['title']}")
            lines.append(f"Source: {article['source']} | Author: {article['author']} | Date: {article['published_date']}")
            lines.append(f"\n{article['summary']}")
            lines.append(f"\nRead more: {article['url']}\n")
    
    lines.append("\n" + "=" * 80)
    lines.append("PowerDigest - Nigeria Power Sector Intelligence")
    lines.append("=" * 80)
    lines.append("\nUnsubscribe: %%UNSUBSCRIBE_URL%%")
    
    return "\n".join(lines)


# =============================================================================
# TEST
# =============================================================================

def main():
    """Test email formatter with sample data"""
    
    # Sample summaries
    sample_summaries = [
        {
            'title': 'Nigeria Loses $300bn to Oil Theft, Senate Demands Action',
            'summary': 'Nigeria has lost approximately $300 billion to oil theft, exposing systemic corruption in the petroleum sector. The Senate recommends creating a special court to prosecute offenders and implementing tighter surveillance to prevent future losses.',
            'impact': 'HIGH',
            'source': 'ElectricityHub',
            'author': 'John Doe',
            'published_date': 'January 15, 2025',
            'url': 'https://theelectricityhub.com/article1'
        },
        {
            'title': 'Kano Government Acquires Additional Shares in KEDCO',
            'summary': 'The Kano State Government has approved plans to acquire majority shares in the Kano Electricity Distribution Company (KEDCO) to improve energy supply, promote industrial growth, and expand electricity access across the state.',
            'impact': 'MEDIUM',
            'source': 'ICIR Nigeria',
            'author': 'Jane Smith',
            'published_date': 'January 14, 2025',
            'url': 'https://www.icirnigeria.org/article2'
        },
        {
            'title': 'TCN Completes Routine Maintenance on Abuja Substation',
            'summary': 'The Transmission Company of Nigeria completed scheduled maintenance work on the Abuja central substation, improving power distribution efficiency in the federal capital territory.',
            'impact': 'LOW',
            'source': 'ElectricityHub',
            'author': 'Mike Johnson',
            'published_date': 'January 13, 2025',
            'url': 'https://theelectricityhub.com/article3'
        }
    ]
    
    # Generate HTML
    html = format_email_html(sample_summaries)
    
    with open('test_email.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    # Generate plain text
    plain = format_plain_text(sample_summaries)
    
    with open('tests/test_email.txt', 'w', encoding='utf-8') as f:
        f.write(plain)
    
    print("✅ Test emails generated:")
    print("   📧 HTML: tests/test_email.html (open in browser)")
    print("   📄 Plain text: tests/test_email.txt")


if __name__ == "__main__":
    main()