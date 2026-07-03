# Multi-Tenant Calculator Architecture Plan

## Overview
Create v2.8.1-multi that inherits all features from v2.8.1 and adds multi-tenant capabilities for multiple branch managers while keeping loan officers' experience frictionless.

## Version Relationship
```
v2.8.1 (Single Admin/Multi-User)
    ↓ (inherits all features + adds multi-tenancy)
v2.8.1-multi (Multi-Tenant)
```

## User Experience Design

### Loan Officers (No Login Required)
- Visit their branch's calculator URL directly
- Use calculator immediately with branch-specific settings
- Branch branding/logo displays automatically
- All calculations use their branch manager's configurations
- **Zero friction - no registration or login needed**

### Branch Managers (Admin Login Only)
- Login only required to access admin panel
- Configure closing costs, branding, settings for their branch
- View their branch's usage statistics only
- Cannot see other branches' data
- Use all existing v2.8.1 admin features but scoped to their organization

### Super Admin (Full Visibility)
- Login to see all branches, statistics, configurations
- Can manage branch managers and their settings
- View aggregated statistics across all branches
- Override any branch settings if needed
- Create/disable branch access

## Technical Implementation

### URL Structure Options

**Option A: Subdomain Approach (Recommended)**
```
branch-abc-mortgage.calculator.com     ← Branch ABC's public calculator
branch-xyz-lending.calculator.com      ← Branch XYZ's public calculator
admin.calculator.com                   ← Super admin dashboard
```

**Option B: Path-Based Approach**
```
calculator.com/abc-mortgage/            ← Branch ABC's public calculator
calculator.com/xyz-lending/             ← Branch XYZ's public calculator
calculator.com/admin/                   ← Super admin dashboard
calculator.com/abc-mortgage/admin/      ← Branch ABC admin panel
```

### Database Structure
```sql
Organizations Table:
- id (primary key)
- name (branch/company name)
- subdomain_slug (for URL routing)
- logo_url (branding)
- theme_colors (JSON for branding)
- active (boolean)
- created_at, updated_at

Branch_Configs Table:
- id (primary key)
- organization_id (foreign key)
- config_type (closing_costs, pmi_rates, mortgage_config, etc.)
- config_data (JSON configuration)
- created_at, updated_at

Usage_Statistics Table:
- id (primary key)
- organization_id (foreign key)
- timestamp
- calculation_data (JSON)
- ip_hash (for anonymous tracking)
- session_id (for grouping calculations)
```

### Features by User Type

#### Public Calculator (No Login)
- Branch-specific branding/logo
- Branch-specific closing costs and configurations
- Anonymous usage tracking (for statistics)
- All v2.8.1 calculator features
- Branch contact information display

#### Branch Manager Admin Panel
- Login required only for admin functions
- Manage their branch's:
  - Closing costs and fees
  - PMI rates
  - Mortgage configurations
  - Branding (logo, colors, contact info)
- View their branch's usage statistics
- Cannot see other branches' data
- All existing v2.8.1 admin features but organization-scoped

#### Super Admin Dashboard
- Manage all organizations (create, edit, disable)
- View consolidated statistics across all branches
- Override any branch settings if needed
- Manage branch manager accounts
- System-wide configuration and maintenance

## Development Workflow
```
1. Develop features in v2.8.1 → Test
2. Merge changes to v2.8.1-multi → Add multi-tenant logic
3. Test multi-tenant scenarios
4. Deploy both versions independently
```

### Implementation Steps for v2.8.1-multi
1. Add organization routing middleware
2. Add branding system (logo, colors, themes)
3. Add multi-tenant data isolation to all admin functions
4. Add super admin dashboard
5. Inherit ALL v2.8.1 features and functionality
6. Add organization-specific statistics tracking
7. Add branch manager account management

## Key Design Principles

### Frictionless Access
- Loan officers never need to login or register
- Calculator works immediately upon visiting branch URL
- No barriers to calculator usage

### Data Isolation
- Branch managers only see their organization's data
- Configurations are completely isolated between branches
- Statistics are tracked per organization

### Complete Inheritance
- Every feature developed in v2.8.1 automatically flows to v2.8.1-multi
- v2.8.1-multi is v2.8.1 + multi-tenant capabilities
- No functionality is lost in the multi-tenant version

### Super Admin Oversight
- Full visibility across all organizations
- Ability to manage and override any settings
- Consolidated reporting and analytics

## Questions for Future Implementation
1. **URL preference**: Subdomain vs Path-based routing
2. **Branding scope**: Logo/colors only vs full theme customization
3. **Statistics detail level**: What granularity for usage analytics
4. **Branch setup process**: Super admin creates vs branch manager self-registration
5. **Custom domains**: Allow branches to use their own domains (branch.com instead of branch.calculator.com)

## Benefits
- **For Loan Officers**: Zero friction, immediate access, branch-specific settings
- **For Branch Managers**: Easy admin control, isolated data, branded experience
- **For Super Admin**: Complete oversight, consolidated management, scalable architecture
- **For Development**: Single codebase maintenance, feature inheritance, clear separation of concerns
