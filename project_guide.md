# Mortgage Loan Calculator App - Project Guidelines

## Overview
This is a comprehensive mortgage calculator application designed to help users analyze mortgage payments, costs, and amortization schedules for both purchase and refinance scenarios. The application provides detailed financial guidance with advanced LTV (Loan-to-Value) calculations and real-time updates.

## Target Users
- **Primary**: Homebuyers and homeowners seeking mortgage information
- **Secondary**: Mortgage brokers and loan officers
- **Tertiary**: Real estate professionals

## Core Features

### Purchase Calculations
- Monthly mortgage payments (Principal & Interest)
- Property tax, PMI, insurance, and HOA fee calculations
- Multiple loan types (Conventional, FHA, VA, USDA)
- Detailed payment breakdowns and amortization schedules
- Closing cost analysis with seller/lender credits

### Refinance Capabilities (Enhanced in v2.5.0)
- **LTV Information Card**: Precise appraised value guidance for different LTV targets
- **Zero Cash to Close**: Calculate loan amounts including all costs and prepaids
- **Real-time Accuracy**: 99.9% accurate LTV calculations using actual current balance
- **No LTV > 80% Blocking**: Fixed validation that incorrectly blocked refinances
- Support for Rate & Term, Cash-Out, and Streamline refinances

### Advanced Features
- JSON-based configuration management
- Admin interface for rate and cost management
- Multiple closing cost scenarios
- Dynamic tax and insurance calculations
- Conservative rounding for user guidance

## Technical Architecture

### Backend (Python/Flask)
- **calculator.py**: Core calculation logic
- **config_manager.py**: Configuration handling
- **admin_logic.py**: Administrative functions
- **chat_routes.py**: AI chat integration
- **mortgage_insurance.py**: PMI calculations
- **financed_fees.py**: Fee calculations

### Frontend (HTML/JavaScript/Bootstrap)
- **templates/index.html**: Main calculator interface
- **static/js/calculator.js**: Frontend calculation logic
- **static/js/ui/**: UI component management
- **static/css/**: Styling and responsive design

### Configuration
- **config/**: JSON configuration files
- **VERSION.py**: Version management
- **logger_config.py**: Logging setup

## Development Standards

### Code Quality
- Follow PEP 8 for Python code
- Use meaningful variable names
- Add docstrings for all functions
- Implement proper error handling
- Write unit tests for critical functions

### Security
- Never expose or log secrets/API keys
- Validate all user inputs
- Use CSRF protection
- Implement proper authentication for admin functions

### Performance
- Optimize calculation algorithms
- Use caching where appropriate
- Minimize database queries
- Implement efficient frontend updates

## Testing Requirements

### Unit Tests
- All calculation functions
- Configuration management
- Input validation
- Error handling scenarios

### Integration Tests
- End-to-end calculation flows
- Admin interface functionality
- Configuration loading
- API endpoints

### User Acceptance Tests
- Purchase calculation accuracy
- Refinance calculation accuracy
- LTV guidance accuracy
- Mobile responsiveness
- Cross-browser compatibility

## Deployment Guidelines

### Environment Setup
- Python 3.8+
- Flask framework
- Bootstrap 5 for UI
- Environment-specific configurations

### Configuration Management
- Use environment variables for sensitive data
- Separate configs for development/production
- Version control for configuration changes

### Monitoring
- Log all calculations and errors
- Monitor performance metrics
- Track user interactions
- Set up alerts for critical issues

## Version Management

### Current Version: 2.5.0
- Major refinance enhancements
- LTV guidance improvements
- Validation fixes
- Enhanced user experience

### Feature Flags
- `refinance_ltv_fix`: Fixed LTV > 80% validation
- `ltv_information_card`: Comprehensive LTV guidance
- `zero_cash_ltv_calculations`: Zero cash to close calculations
- `actual_current_balance_integration`: Real-time accuracy
- `conservative_ltv_rounding`: User-friendly rounding

## Success Metrics

### Accuracy Metrics
- LTV calculation accuracy: 99.9% (target)
- Payment calculation accuracy: 100% (required)
- Closing cost accuracy: 95%+ (target)

### User Experience Metrics
- Page load time: <3 seconds
- Calculation response time: <1 second
- Mobile responsiveness: 100% functional
- Cross-browser compatibility: 95%+ browsers

### Business Metrics
- User engagement: Time on site
- Feature adoption: Usage of advanced features
- Error rates: <1% calculation errors
- User satisfaction: Feedback scores

## Future Enhancements

### Planned Features
- Advanced amortization scenarios
- Comparative analysis tools
- Export capabilities (PDF, Excel)
- Integration with real estate APIs
- Multi-language support

### Technical Improvements
- API development for third-party integration
- Enhanced mobile experience
- Real-time market data integration
- Advanced analytics and reporting

## Support and Maintenance

### Regular Tasks
- Update interest rates and fees
- Monitor calculation accuracy
- Review user feedback
- Security updates
- Performance optimization

### Emergency Procedures
- Calculation error response
- System downtime procedures
- Data backup and recovery
- Security incident response

## Documentation Standards

### Code Documentation
- Inline comments for complex logic
- Function docstrings with parameters
- Module-level documentation
- API documentation

### User Documentation
- Feature explanations
- Calculation methodologies
- Troubleshooting guides
- FAQ sections

### Technical Documentation
- Architecture diagrams
- Database schemas
- API specifications
- Deployment procedures

## Compliance and Legal

### Financial Calculations
- Ensure TILA compliance where applicable
- Provide clear disclaimers
- Maintain calculation transparency
- Regular accuracy audits

### Data Protection
- Implement privacy protection
- Secure data handling
- Clear data usage policies
- GDPR compliance considerations

## Contact and Support

### Development Team
- Primary Developer: [Contact Information]
- Project Manager: [Contact Information]
- QA Lead: [Contact Information]

### Business Stakeholders
- Product Owner: [Contact Information]
- Business Analyst: [Contact Information]
- End User Representative: [Contact Information]

---

**Document Version**: 1.0  
**Last Updated**: July 2, 2025  
**Next Review**: TBD based on project needs