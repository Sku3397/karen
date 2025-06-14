"""
Migration 004: Service Catalog Schema
DATABASE-004 Implementation

Creates comprehensive service catalog with pricing tiers, availability windows,
seasonal adjustments, service categories, and dynamic pricing rules.
"""

from datetime import datetime
from google.cloud import firestore
import logging

logger = logging.getLogger(__name__)

def up(db: firestore.Client):
    """Apply migration - create service catalog schema"""
    print("🔄 Running migration 004: Service Catalog Schema")
    
    # Create service categories
    service_categories = [
        {
            'id': 'cat_plumbing',
            'name': 'Plumbing',
            'description': 'Water-related repairs and installations',
            'icon': 'plumbing',
            'color': '#2196F3',
            'display_order': 1,
            'is_active': True,
            'requires_license': True,
            'emergency_available': True,
            'typical_duration_range': {'min': 30, 'max': 240},
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP
        },
        {
            'id': 'cat_electrical',
            'name': 'Electrical',
            'description': 'Electrical repairs and installations',
            'icon': 'electrical',
            'color': '#FF9800',
            'display_order': 2,
            'is_active': True,
            'requires_license': True,
            'emergency_available': True,
            'typical_duration_range': {'min': 45, 'max': 300},
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP
        },
        {
            'id': 'cat_hvac',
            'name': 'HVAC',
            'description': 'Heating, ventilation, and air conditioning',
            'icon': 'hvac',
            'color': '#4CAF50',
            'display_order': 3,
            'is_active': True,
            'requires_license': True,
            'emergency_available': True,
            'typical_duration_range': {'min': 60, 'max': 480},
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP
        },
        {
            'id': 'cat_general_repair',
            'name': 'General Repairs',
            'description': 'Drywall, painting, and general handyman services',
            'icon': 'tools',
            'color': '#9C27B0',
            'display_order': 4,
            'is_active': True,
            'requires_license': False,
            'emergency_available': False,
            'typical_duration_range': {'min': 30, 'max': 180},
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP
        }
    ]
    
    # Create service categories
    for category in service_categories:
        cat_ref = db.collection('service_categories').document(category['id'])
        cat_ref.set(category)
    
    print(f"✅ Created {len(service_categories)} service categories")
    
    # Create core services
    services = [
        {
            'id': 'svc_faucet_repair',
            'category_id': 'cat_plumbing',
            'name': 'Faucet Repair',
            'short_description': 'Fix leaky or broken faucets',
            'detailed_description': 'Comprehensive faucet repair including cartridge replacement, seal repair, and handle adjustment. Covers kitchen and bathroom faucets.',
            'service_type': 'repair',
            'complexity_level': 'basic',
            'estimated_duration_minutes': 90,
            'duration_range': {'min': 60, 'max': 120},
            
            # Pricing Structure
            'base_price': 85.00,
            'hourly_rate': 95.00,
            'materials_markup': 0.15,  # 15% markup on materials
            'pricing_type': 'fixed_base_plus_materials',
            
            # Pricing Tiers
            'pricing_tiers': {
                'basic': {
                    'name': 'Basic Repair',
                    'price': 85.00,
                    'includes': ['Labor for standard repair', 'Basic seals and washers', 'Up to 1 hour service'],
                    'excludes': ['Major part replacement', 'Emergency service']
                },
                'standard': {
                    'name': 'Standard Repair',
                    'price': 125.00,
                    'includes': ['Labor for complex repair', 'Standard replacement parts', 'Up to 2 hours service', 'Minor adjustments'],
                    'excludes': ['Complete faucet replacement', 'Emergency service']
                },
                'premium': {
                    'name': 'Complete Service',
                    'price': 200.00,
                    'includes': ['Full diagnostic', 'Any necessary repairs', 'Quality replacement parts', 'Up to 3 hours service', '30-day guarantee'],
                    'excludes': ['New faucet installation']
                }
            },
            
            # Availability
            'availability': {
                'standard_hours': {
                    'monday': {'start': '08:00', 'end': '18:00'},
                    'tuesday': {'start': '08:00', 'end': '18:00'},
                    'wednesday': {'start': '08:00', 'end': '18:00'},
                    'thursday': {'start': '08:00', 'end': '18:00'},
                    'friday': {'start': '08:00', 'end': '18:00'},
                    'saturday': {'start': '09:00', 'end': '15:00'},
                    'sunday': None
                },
                'emergency_available': True,
                'emergency_hours': '24/7',
                'emergency_surcharge': 0.5,  # 50% surcharge
                'same_day_available': True,
                'same_day_surcharge': 0.25,  # 25% surcharge
                'booking_lead_time_hours': 2
            },
            
            # Requirements
            'requirements': {
                'tools_required': ['adjustable_wrench', 'screwdriver_set', 'pliers', 'pipe_wrench'],
                'materials_commonly_needed': ['o_rings', 'washers', 'cartridges', 'packing'],
                'skill_level_required': 'intermediate',
                'license_required': False,
                'insurance_coverage': 'general_liability',
                'safety_equipment': ['safety_glasses', 'gloves']
            },
            
            # Service Features
            'features': {
                'warranty_period_days': 30,
                'parts_warranty_days': 90,
                'follow_up_included': True,
                'photo_documentation': True,
                'before_after_photos': True,
                'customer_approval_required': False,
                'estimate_required_above': 150.00
            },
            
            # SEO and Marketing
            'seo_keywords': ['faucet repair', 'leaky faucet', 'dripping faucet', 'kitchen faucet', 'bathroom faucet'],
            'popular_keywords': ['fix leaky faucet', 'faucet won\'t turn off', 'faucet handle loose'],
            'seasonal_demand': {
                'spring': 'high',
                'summer': 'medium',
                'fall': 'medium', 
                'winter': 'high'
            },
            
            # Status
            'status': 'active',
            'is_featured': True,
            'display_order': 1,
            'last_price_update': firestore.SERVER_TIMESTAMP,
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP,
            'created_by': 'system',
            'updated_by': 'system'
        },
        {
            'id': 'svc_toilet_repair',
            'category_id': 'cat_plumbing',
            'name': 'Toilet Repair',
            'short_description': 'Fix running, clogged, or leaking toilets',
            'detailed_description': 'Complete toilet repair service including flapper replacement, fill valve repair, wax ring replacement, and unclogging.',
            'service_type': 'repair',
            'complexity_level': 'intermediate',
            'estimated_duration_minutes': 120,
            'duration_range': {'min': 60, 'max': 180},
            
            'base_price': 115.00,
            'hourly_rate': 95.00,
            'materials_markup': 0.15,
            'pricing_type': 'fixed_base_plus_materials',
            
            'pricing_tiers': {
                'basic': {
                    'name': 'Basic Toilet Repair',
                    'price': 115.00,
                    'includes': ['Running toilet fix', 'Flapper replacement', 'Chain adjustment', 'Up to 1.5 hours'],
                    'excludes': ['Major clogs', 'Wax ring replacement']
                },
                'standard': {
                    'name': 'Standard Toilet Service',
                    'price': 165.00,
                    'includes': ['Complete internal repair', 'Fill valve replacement', 'Minor clog clearing', 'Up to 2.5 hours'],
                    'excludes': ['Toilet removal/reinstall', 'Sewer line issues']
                },
                'comprehensive': {
                    'name': 'Complete Toilet Service',
                    'price': 285.00,
                    'includes': ['Full toilet service', 'Wax ring replacement', 'Toilet removal/reinstall', 'Major clog clearing', 'Up to 4 hours'],
                    'excludes': ['New toilet installation', 'Sewer main issues']
                }
            },
            
            'availability': {
                'standard_hours': {
                    'monday': {'start': '08:00', 'end': '18:00'},
                    'tuesday': {'start': '08:00', 'end': '18:00'},
                    'wednesday': {'start': '08:00', 'end': '18:00'},
                    'thursday': {'start': '08:00', 'end': '18:00'},
                    'friday': {'start': '08:00', 'end': '18:00'},
                    'saturday': {'start': '09:00', 'end': '15:00'},
                    'sunday': None
                },
                'emergency_available': True,
                'emergency_hours': '24/7',
                'emergency_surcharge': 0.5,
                'same_day_available': True,
                'same_day_surcharge': 0.25,
                'booking_lead_time_hours': 2
            },
            
            'requirements': {
                'tools_required': ['adjustable_wrench', 'toilet_auger', 'plunger', 'wax_ring_remover'],
                'materials_commonly_needed': ['flapper', 'fill_valve', 'wax_ring', 'toilet_bolts'],
                'skill_level_required': 'intermediate',
                'license_required': False,
                'insurance_coverage': 'general_liability',
                'safety_equipment': ['gloves', 'knee_pads']
            },
            
            'features': {
                'warranty_period_days': 30,
                'parts_warranty_days': 90,
                'follow_up_included': True,
                'photo_documentation': True,
                'before_after_photos': True,
                'customer_approval_required': False,
                'estimate_required_above': 200.00
            },
            
            'seo_keywords': ['toilet repair', 'running toilet', 'toilet won\'t flush', 'toilet clog', 'toilet leak'],
            'popular_keywords': ['toilet keeps running', 'toilet overflow', 'toilet won\'t stop running'],
            'seasonal_demand': {
                'spring': 'medium',
                'summer': 'high',
                'fall': 'medium',
                'winter': 'medium'
            },
            
            'status': 'active',
            'is_featured': True,
            'display_order': 2,
            'last_price_update': firestore.SERVER_TIMESTAMP,
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP,
            'created_by': 'system',
            'updated_by': 'system'
        },
        {
            'id': 'svc_outlet_installation',
            'category_id': 'cat_electrical',
            'name': 'Electrical Outlet Installation',
            'short_description': 'Install new electrical outlets and switches',
            'detailed_description': 'Professional installation of standard and GFCI outlets, switches, and USB outlets. Includes running new wiring when needed.',
            'service_type': 'installation',
            'complexity_level': 'advanced',
            'estimated_duration_minutes': 180,
            'duration_range': {'min': 120, 'max': 300},
            
            'base_price': 150.00,
            'hourly_rate': 125.00,
            'materials_markup': 0.20,
            'pricing_type': 'hourly_plus_materials',
            
            'pricing_tiers': {
                'basic': {
                    'name': 'Standard Outlet',
                    'price': 150.00,
                    'includes': ['Standard outlet installation', 'Existing wire connection', 'Up to 2 hours labor'],
                    'excludes': ['New wiring runs', 'GFCI outlets', 'Panel work']
                },
                'gfci': {
                    'name': 'GFCI Outlet',
                    'price': 185.00,
                    'includes': ['GFCI outlet installation', 'Safety testing', 'Code compliance', 'Up to 2.5 hours labor'],
                    'excludes': ['New circuit installation', 'Panel modifications']
                },
                'new_circuit': {
                    'name': 'New Circuit Installation',
                    'price': 350.00,
                    'includes': ['New circuit from panel', 'Outlet installation', 'Wire fishing', 'Code compliance', 'Up to 5 hours labor'],
                    'excludes': ['Panel upgrades', 'Permit fees']
                }
            },
            
            'availability': {
                'standard_hours': {
                    'monday': {'start': '08:00', 'end': '17:00'},
                    'tuesday': {'start': '08:00', 'end': '17:00'},
                    'wednesday': {'start': '08:00', 'end': '17:00'},
                    'thursday': {'start': '08:00', 'end': '17:00'},
                    'friday': {'start': '08:00', 'end': '17:00'},
                    'saturday': {'start': '09:00', 'end': '14:00'},
                    'sunday': None
                },
                'emergency_available': False,
                'same_day_available': False,
                'booking_lead_time_hours': 24
            },
            
            'requirements': {
                'tools_required': ['wire_strippers', 'voltage_tester', 'drill', 'fish_tape', 'electrical_pliers'],
                'materials_commonly_needed': ['outlet', 'wire_nuts', 'romex_wire', 'outlet_box'],
                'skill_level_required': 'expert',
                'license_required': True,
                'insurance_coverage': 'electrical_liability',
                'safety_equipment': ['insulated_gloves', 'safety_glasses', 'voltage_tester']
            },
            
            'features': {
                'warranty_period_days': 90,
                'parts_warranty_days': 365,
                'follow_up_included': True,
                'photo_documentation': True,
                'before_after_photos': True,
                'customer_approval_required': True,
                'estimate_required_above': 300.00,
                'permit_required': True
            },
            
            'seo_keywords': ['outlet installation', 'electrical outlet', 'GFCI outlet', 'new outlet', 'outlet repair'],
            'popular_keywords': ['add outlet', 'install GFCI', 'kitchen outlet', 'bathroom outlet'],
            'seasonal_demand': {
                'spring': 'high',
                'summer': 'medium',
                'fall': 'medium',
                'winter': 'low'
            },
            
            'status': 'active',
            'is_featured': False,
            'display_order': 5,
            'last_price_update': firestore.SERVER_TIMESTAMP,
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP,
            'created_by': 'system',
            'updated_by': 'system'
        }
    ]
    
    # Create service documents
    for service in services:
        svc_ref = db.collection('services').document(service['id'])
        svc_ref.set(service)
    
    print(f"✅ Created {len(services)} service documents")
    
    # Create seasonal pricing rules
    seasonal_pricing = [
        {
            'id': 'seasonal_hvac_summer',
            'name': 'Summer HVAC Surge',
            'service_category_ids': ['cat_hvac'],
            'season': 'summer',
            'months': [6, 7, 8],
            'price_multiplier': 1.15,
            'is_active': True,
            'start_date': '2025-06-01',
            'end_date': '2025-08-31',
            'description': 'Increased pricing during peak AC season',
            'created_at': firestore.SERVER_TIMESTAMP
        },
        {
            'id': 'seasonal_plumbing_winter',
            'name': 'Winter Emergency Plumbing',
            'service_category_ids': ['cat_plumbing'],
            'season': 'winter',
            'months': [12, 1, 2],
            'price_multiplier': 1.10,
            'is_active': True,
            'start_date': '2024-12-01',
            'end_date': '2025-02-28',
            'description': 'Increased pricing for winter pipe emergencies',
            'created_at': firestore.SERVER_TIMESTAMP
        }
    ]
    
    # Create seasonal pricing documents
    for pricing in seasonal_pricing:
        price_ref = db.collection('seasonal_pricing').document(pricing['id'])
        price_ref.set(pricing)
    
    print(f"✅ Created {len(seasonal_pricing)} seasonal pricing rules")
    
    # Create service packages/bundles
    service_packages = [
        {
            'id': 'pkg_bathroom_complete',
            'name': 'Complete Bathroom Service',
            'description': 'Full bathroom maintenance package including plumbing and electrical',
            'service_ids': ['svc_faucet_repair', 'svc_toilet_repair', 'svc_outlet_installation'],
            'package_price': 450.00,
            'individual_price_total': 500.00,
            'savings_amount': 50.00,
            'savings_percentage': 0.10,
            'estimated_duration_minutes': 360,
            'is_active': True,
            'package_type': 'maintenance',
            'features': {
                'warranty_period_days': 45,
                'discount_on_future_services': 0.05,
                'priority_scheduling': True
            },
            'created_at': firestore.SERVER_TIMESTAMP
        }
    ]
    
    # Create service packages
    for package in service_packages:
        pkg_ref = db.collection('service_packages').document(package['id'])
        pkg_ref.set(package)
    
    print(f"✅ Created {len(service_packages)} service packages")
    
    # Create service catalog analytics
    catalog_analytics = {
        'type': 'service_catalog_metrics',
        'data': {
            'total_services': len(services),
            'total_categories': len(service_categories),
            'active_services': len([s for s in services if s['status'] == 'active']),
            'featured_services': len([s for s in services if s.get('is_featured', False)]),
            'pricing_distribution': {
                'under_100': len([s for s in services if s['base_price'] < 100]),
                '100_to_200': len([s for s in services if 100 <= s['base_price'] < 200]),
                'over_200': len([s for s in services if s['base_price'] >= 200])
            },
            'by_category': {
                cat['id']: len([s for s in services if s['category_id'] == cat['id']]) 
                for cat in service_categories
            },
            'complexity_distribution': {
                'basic': len([s for s in services if s['complexity_level'] == 'basic']),
                'intermediate': len([s for s in services if s['complexity_level'] == 'intermediate']),
                'advanced': len([s for s in services if s['complexity_level'] == 'advanced'])
            }
        },
        'calculated_at': firestore.SERVER_TIMESTAMP,
        'metadata': {
            'migration': '004_service_catalog_schema',
            'sample_data': True
        }
    }
    
    analytics_ref = db.collection('service_analytics').document('catalog_overview')
    analytics_ref.set(catalog_analytics)
    print("✅ Created service catalog analytics document")
    
    # Create migration tracking document
    migration_ref = db.collection('_migrations').document('004_service_catalog_schema')
    migration_ref.set({
        'migration_id': '004_service_catalog_schema',
        'applied_at': firestore.SERVER_TIMESTAMP,
        'status': 'completed',
        'description': 'Service catalog schema with categories, pricing, and availability',
        'collections_created': [
            'service_categories',
            'services',
            'seasonal_pricing',
            'service_packages',
            'service_analytics'
        ],
        'documents_created': len(service_categories) + len(services) + len(seasonal_pricing) + len(service_packages) + 2
    })
    
    print("✅ Migration 004 completed successfully")

def down(db: firestore.Client):
    """Rollback migration - remove service catalog schema"""
    print("🔄 Rolling back migration 004: Service Catalog Schema")
    
    # Remove all documents from collections
    collections_to_clear = [
        ('service_categories', ['cat_plumbing', 'cat_electrical', 'cat_hvac', 'cat_general_repair']),
        ('services', ['svc_faucet_repair', 'svc_toilet_repair', 'svc_outlet_installation']),
        ('seasonal_pricing', ['seasonal_hvac_summer', 'seasonal_plumbing_winter']),
        ('service_packages', ['pkg_bathroom_complete']),
        ('service_analytics', ['catalog_overview'])
    ]
    
    for collection_name, doc_ids in collections_to_clear:
        for doc_id in doc_ids:
            doc_ref = db.collection(collection_name).document(doc_id)
            if doc_ref.get().exists:
                doc_ref.delete()
                print(f"✅ Removed {collection_name} document: {doc_id}")
    
    # Remove migration tracking document
    migration_ref = db.collection('_migrations').document('004_service_catalog_schema')
    if migration_ref.get().exists:
        migration_ref.delete()
        print("✅ Removed migration tracking document")
    
    print("✅ Migration 004 rollback completed")

if __name__ == "__main__":
    from src.firebase_setup import setup_firebase
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python migrations/004_service_catalog_schema.py [up|down]")
        sys.exit(1)
    
    action = sys.argv[1].lower()
    
    try:
        db = setup_firebase()
        
        if action == 'up':
            up(db)
        elif action == 'down':
            down(db)
        else:
            print("Invalid action. Use 'up' or 'down'")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        print(f"Migration failed: {e}")
        sys.exit(1)