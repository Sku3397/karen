export NODE_OPTIONS="--max-old-space-size=4096"
export JAVA_OPTS="-Xmx4g -Xms2g"
export PYTHONUNBUFFERED=1

echo "✅ Memory optimizations configured:"
echo "  NODE_OPTIONS=$NODE_OPTIONS"
echo "  JAVA_OPTS=$JAVA_OPTS"
echo "  PYTHONUNBUFFERED=$PYTHONUNBUFFERED"

# Test NLP integration
echo "🧪 Testing NLP integration..."
python3 -c "
import sys
sys.path.insert(0, src)
try:
    from src.nlp_engine import get_nlp_engine
    print(✅ NLP engine imported successfully)
except Exception as e:
    print(f❌ NLP engine import failed: {e})
"

echo ""
echo "🎉 Environment setup complete\!"
echo "Next steps:"
echo "1. Run: python3 test_nlp_integration.py"
echo "2. Start services: npm install && npm start"
echo "3. Monitor: docker-compose up -d redis"

